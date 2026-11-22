"""Audit whether the pretrained rubric router uses its reward-input magnitudes."""
import json

import numpy as np

import rubric_conditioned_routing as experiment

route = experiment.route


def state_map(order):
    return np.asarray([sum(1 << order[i] for i in range(3) if mask & (1 << i))
                       for mask in route.STATES])


def remapped_mean_policy(net, average, actual):
    import torch

    _, order = experiment.canonical(actual)
    with torch.inference_mode():
        left, right = net(torch.as_tensor(average / experiment.SCALE, dtype=torch.float32)).numpy().reshape(2, 8, 4, 4)
    acts = np.where(route.JOINT, left, -np.inf).reshape(8, 16).argmax(-1)
    reply = np.where(route.SEND[:, None, :], right, -np.inf).argmax(-1)
    return experiment.remap_policy((acts // 4, acts % 4, reply), order)


def audit():
    import torch

    torch.set_num_threads(1)
    data = json.loads((experiment.OUT / "report.json").read_text())
    weights = experiment.OUT / "weights.pt"
    assert experiment.space.runner.digest(weights) == data["weights_sha256"]
    net = torch.nn.Sequential(torch.nn.Linear(8, 48), torch.nn.Tanh(), torch.nn.Linear(48, 48), torch.nn.Tanh(),
                              torch.nn.Linear(48, 256))
    net.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
    net.eval()
    train = np.asarray(data["training_rewards"])
    assert np.array_equal(train, experiment.training_values())
    average = train.mean(axis=0)
    result = {}
    for name, checksum, intended, observed in experiment.held_out():
        source = data["held_out"][name]
        assert checksum == source["source_sha256"]
        actual = experiment.choose(net, intended)
        assert [p.tolist() for p in actual] == source["greedy_policy"]
        standard = remapped_mean_policy(net, average, intended)
        entry = {}
        for prior_name, prior in route.TEST_PRIORS.items():
            references = source["priors"][prior_name]
            measured = route.evaluate(actual, prior, observed, route.TRAIN_LOSS)["net"]
            assert abs(measured - references["fit"]["net"]) < 1e-9
            transformed = []
            for order in experiment.ORDERS:
                idx = state_map(order)
                policy = experiment.choose(net, intended[idx])
                paired_prior = prior[np.ix_(idx, idx)]
                net_value = route.evaluate(policy, paired_prior, observed[idx], route.TRAIN_LOSS)["net"]
                transformed.append(net_value)
            normal = route.evaluate(standard, prior, observed, route.TRAIN_LOSS)["net"]
            entry[prior_name] = {"fit": measured, "canonicalization_plus_constant_input": normal,
                                 "independent": references["independent"]["net"],
                                 "varying_input_advantage": measured - normal,
                                 "relabeled": transformed}
        result[name] = {"identical_greedy_tables_with_constant_input": all(np.array_equal(x, y) for x, y in
                                                                          zip(actual, standard, strict=True)),
                        "conditioned": entry}
    return {"scope": "Frozen weights, historical bank replay. The constant-input control retains "
                     "case-specific role canonicalization. Relabeling permutes the rubric, inventories and "
                     "realized reward together.",
            "weights_sha256": data["weights_sha256"], "train_mean_canonical_rubric": average.tolist(), "cases": result}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
