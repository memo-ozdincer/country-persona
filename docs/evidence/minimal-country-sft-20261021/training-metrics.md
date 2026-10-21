# Full recorded training metrics

[Evidence index](README.md)

Three fresh Qwen3.5-4B rank-8 LoRA SFT fits. BF16; alpha 16; dropout 0.05; all linear layers; AdamW; peak learning rate 5e-5 with linear decay; microbatch one; accumulation two; seed 42; completion-only loss; no packing. Context 4,096 tokens; greedy generation with thinking disabled; output cap 384. Hardware: NVIDIA RTX PRO 6000 Blackwell Server Edition.

Changing the step budget also changes the learning-rate schedule. No intermediate answers, intermediate adapter checkpoints, or exact per-step sample-order log were saved. All recorded optimizer metrics and gradient checks are preserved below.

## Four examples · 16 steps

Training-target NLL: **2.895686 → 1.678180**. Training time: **25.38 seconds**; peak allocation: **9.39 GiB**. Actual sequence/supervised tokens: **41,928 / 3,400**.

| Step | Epoch | Logged loss | Learning rate | Logged grad norm | Finite grads | Post-clipping gradient L2 |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 0.5 | 2.885 | 5e-05 | 4.584 | True | 0.9999997622185505 |
| 2 | 1 | 2.873 | 4.688e-05 | 4.44 | True | 0.9999998037920803 |
| 3 | 1.5 | 2.757 | 4.375e-05 | 4.174 | True | 0.999999684819921 |
| 4 | 2 | 2.524 | 4.063e-05 | 3.895 | True | 0.9999997000265968 |
| 5 | 2.5 | 2.244 | 3.75e-05 | 3.766 | True | 0.9999998162863114 |
| 6 | 3 | 2.438 | 3.438e-05 | 3.175 | True | 0.999999686144361 |
| 7 | 3.5 | 1.962 | 3.125e-05 | 3.071 | True | 0.999999660499445 |
| 8 | 4 | 2.244 | 2.813e-05 | 3.055 | True | 0.9999997449607116 |
| 9 | 4.5 | 2.165 | 2.5e-05 | 3.166 | True | 0.9999996623516176 |
| 10 | 5 | 1.721 | 2.187e-05 | 2.679 | True | 0.9999995797252936 |
| 11 | 5.5 | 1.663 | 1.875e-05 | 2.621 | True | 0.999999662191486 |
| 12 | 6 | 1.992 | 1.563e-05 | 2.787 | True | 0.9999996758631381 |
| 13 | 6.5 | 1.771 | 1.25e-05 | 2.71 | True | 0.9999996760343989 |
| 14 | 7 | 1.723 | 9.375e-06 | 2.532 | True | 0.9999996376791046 |
| 15 | 7.5 | 1.703 | 6.25e-06 | 2.487 | True | 0.9999996899767671 |
| 16 | 8 | 1.693 | 3.125e-06 | 2.709 | True | 0.9999996764757093 |

<details>
<summary>Full configuration, masks, per-target losses, gradient traces and saved-weight checks</summary>

````json
{
  "status": "completed",
  "mode": "fit",
  "question": "Does shortening complete source-to-response supervision to four examples and exposing each eight times produce useful fidelity, rather than merely lowering loss?",
  "identity": {
    "host": "aurora",
    "pid": 354481,
    "process_start_ticks": 1149246176,
    "process_start_utc": "2026-10-05T21:40:51.760000+00:00",
    "command": [
      "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python",
      "scripts/run_minimal_country_checkpoint.py",
      "--mode",
      "fit",
      "--config",
      "configs/posttraining/qwen35-minimal-country-20261005-v2.json",
      "--gpu-uuid",
      "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
      "--output",
      "runs/aurora-minimal-country-fit-20261005-v3"
    ],
    "cwd": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1",
    "slurm_job_id": null
  },
  "gpu": {
    "uuid": "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
    "name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
    "memory_used_mib_before_launch": 0,
    "utilization_before_launch": 0,
    "existing_compute_processes": []
  },
  "run_directory": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1/runs/aurora-minimal-country-fit-20261005-v3",
  "created_at": "2026-10-05T21:40:53.192581+00:00",
  "config": {
    "model": "Qwen/Qwen3.5-4B",
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "model_path": "/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "runtime_path": "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1",
    "runtime_pins": {
      "torch": "2.8.0+cu128",
      "transformers": "5.17.0",
      "trl": "1.14.1",
      "peft": "0.21.1",
      "datasets": "5.0.1",
      "accelerate": "1.15.0"
    },
    "seed": 42,
    "chat_template_kwargs": {
      "enable_thinking": false
    },
    "max_length": 4096,
    "generation_max_new_tokens": 384,
    "max_steps": 16,
    "gradient_accumulation_steps": 2,
    "lora_rank": 8,
    "learning_rate": 5e-05,
    "pack": "data/prepared/minimal-country-20261005-v1",
    "baseline_run": "runs/aurora-minimal-country-base-20261005-v2",
    "kind": "four_complete_short_targets_source_conditioned",
    "authorization": "User explicitly requests recursive minimal country pipeline experiments, complete selected-data reading, inspection then scale.",
    "change_from_v1": "Materialize JSONL iterator as a list before token audit and Dataset.from_list. Rerun base with identical generation protocol; failed v2 fit made zero optimizer steps."
  },
  "config_sha256": "75dc1bd7187475cac9988bcae85f291d654af98e30096687764137e878c1daec",
  "pack_manifest_sha256": "3a268230e774872105e4c8ec1ea0c049fea8f54b1969d1955ecd01c7c66e9a59",
  "manual_inspection_sha256": "f090fe2a415152c3f106d2fac7f209bbd3418d00c3ef3aeee60a4d7fff4a9211",
  "source_code_sha256": {
    "scripts/run_minimal_country_checkpoint.py": "fd788d512b148095e0fd6dc3f37274f7cb0efb04f32126df881e66b9dc2f5a79",
    "scripts/run_aurora_qwen35_smoke.py": "cfb8cd73f157aea2f50dec8e095bee608d4a01d1b44196cee7b3656302818603",
    "src/country_persona/training_checks.py": "6c4e5e38cc9bf8c000af1698ee7fdda9683e9350c6a19d1c934ebec43a52d7e6"
  },
  "scope": "Inspect matched base first. Fit only on a real observed gap; then inspect all outputs before adding scope or optimization.",
  "independent_review_complete": false,
  "nccl_tested": false,
  "versions": {
    "torch": "2.8.0+cu128",
    "transformers": "5.17.0",
    "trl": "1.14.1",
    "peft": "0.21.1",
    "datasets": "5.0.1",
    "accelerate": "1.15.0"
  },
  "model_verification": {
    "receipt_sha256": "9232b2bce9177f1fd63538f1e59dbf8989e32fa0a208128a89cb7300e6f12011",
    "files_rehashed": 11,
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "files": {
      "chat_template.jinja": {
        "bytes": 7756,
        "sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
        "hub_hash": "a585dec894e63da457d9440ec6aa7caa16d20860",
        "verification": "hub_git_blob_sha1"
      },
      "config.json": {
        "bytes": 3161,
        "sha256": "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670",
        "hub_hash": "557d961b205319c6a7da5f757f565b69b3967b7d",
        "verification": "hub_git_blob_sha1"
      },
      "merges.txt": {
        "bytes": 3353259,
        "sha256": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
        "hub_hash": "a494e019ca1502219fd0128658b979e5f05ae8e8",
        "verification": "hub_git_blob_sha1"
      },
      "model.safetensors-00001-of-00002.safetensors": {
        "bytes": 5329398688,
        "sha256": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "hub_hash": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors-00002-of-00002.safetensors": {
        "bytes": 3990429408,
        "sha256": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "hub_hash": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors.index.json": {
        "bytes": 76196,
        "sha256": "cf3f798ee02ba45f9622aa8892a47369ab667d0afbf154ee7c2212de42e6302d",
        "hub_hash": "fddda6039f7c1d17260c9e923b8a72fd025d9a86",
        "verification": "hub_git_blob_sha1"
      },
      "preprocessor_config.json": {
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "hub_hash": "2ea84a437d448ff71b08df68fdd949d5cc4ebb64",
        "verification": "hub_git_blob_sha1"
      },
      "tokenizer.json": {
        "bytes": 12807982,
        "sha256": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "hub_hash": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "verification": "hub_lfs_sha256"
      },
      "tokenizer_config.json": {
        "bytes": 16710,
        "sha256": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8",
        "hub_hash": "eda48d3e75a8e59a8479ee4ec8b37f76e711d9c1",
        "verification": "hub_git_blob_sha1"
      },
      "video_preprocessor_config.json": {
        "bytes": 385,
        "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
        "hub_hash": "3ba673a5ad7d4d13f54155ecd38b2a94a6dac8fe",
        "verification": "hub_git_blob_sha1"
      },
      "vocab.json": {
        "bytes": 6722759,
        "sha256": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
        "hub_hash": "0aa0ce0658d60ac4a5d609f4eadb0e8e43514176",
        "verification": "hub_git_blob_sha1"
      }
    }
  },
  "tokenization": [
    {
      "sequence_tokens": 1303,
      "target_tokens": 100
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 110
    },
    {
      "sequence_tokens": 1312,
      "target_tokens": 107
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 108
    }
  ],
  "text_model_loading": {
    "missing_keys": [],
    "unexpected_keys": [],
    "mismatched_keys": [],
    "error_msgs": []
  },
  "baseline_inspection_sha256": "5fde0e5a5f995cb283b2c5fdd8b9e05d59c9495c3bc9a30329a60520fdc30d54",
  "mask_audit": {
    "rows": 4,
    "sequence_tokens_once": 5241,
    "supervised_tokens_once": 425,
    "actual_trainer_masks_checked": true
  },
  "loss_before": {
    "rows": [
      {
        "loss": 2.749253511428833,
        "supervised_tokens": 100
      },
      {
        "loss": 3.046025037765503,
        "supervised_tokens": 110
      },
      {
        "loss": 3.012132406234741,
        "supervised_tokens": 107
      },
      {
        "loss": 2.762781858444214,
        "supervised_tokens": 108
      }
    ],
    "token_weighted_loss": 2.8956863846498377,
    "scope": "same_training_targets_not_generalization"
  },
  "optimization_checks": {
    "all_ranks_participated": true,
    "rank_count": 1,
    "all_ranks_same_final_adapter": true,
    "rank_checks": [
      {
        "rank": 0,
        "steps": 16,
        "training_loss": 2.147333547472954,
        "actual_sequence_tokens": 41928,
        "actual_target_tokens": 3400,
        "gradient_checks": 16,
        "gradient_trace": [
          {
            "step": 1,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997622185505
          },
          {
            "step": 2,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998037920803
          },
          {
            "step": 3,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999684819921
          },
          {
            "step": 4,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997000265968
          },
          {
            "step": 5,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998162863114
          },
          {
            "step": 6,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999686144361
          },
          {
            "step": 7,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999660499445
          },
          {
            "step": 8,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997449607116
          },
          {
            "step": 9,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996623516176
          },
          {
            "step": 10,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995797252936
          },
          {
            "step": 11,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999662191486
          },
          {
            "step": 12,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996758631381
          },
          {
            "step": 13,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996760343989
          },
          {
            "step": 14,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996376791046
          },
          {
            "step": 15,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996899767671
          },
          {
            "step": 16,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996764757093
          }
        ],
        "adapter_tensors": 496,
        "changed_adapter_tensors": 496,
        "adapter_update_l2": 1.1017779847674638,
        "all_adapter_tensors_finite": true,
        "initial_adapter_digest": "6372b4c0d640d45fa81bd7c79ac522485dbe96a79b8369fd422a2c4a698b2772",
        "final_adapter_digest": "19656fb0a765e411da7a095d3f7bd6aaf7ec34e7372d55c44b0a1a11e9a50b8b"
      }
    ]
  },
  "training_seconds": 25.379074692726135,
  "peak_allocated_gpu_gib": 9.38941240310669,
  "loss_after": {
    "rows": [
      {
        "loss": 1.4175747632980347,
        "supervised_tokens": 100
      },
      {
        "loss": 1.9177124500274658,
        "supervised_tokens": 110
      },
      {
        "loss": 1.8059130907058716,
        "supervised_tokens": 107
      },
      {
        "loss": 1.5489617586135864,
        "supervised_tokens": 108
      }
    ],
    "token_weighted_loss": 1.6781798034555773,
    "scope": "same_training_targets_not_generalization"
  },
  "serialization_checks": {
    "saved_tensors_equal": true,
    "reload_verified_after_state_perturbation": true,
    "same_base_probe_logits_equal": true,
    "probe_tokens": 32,
    "maximum_logit_difference": 0.0,
    "logit_atol": 1e-05,
    "logit_rtol": 1e-05,
    "files_sha256": {
      "adapter_model.safetensors": "4cfdcfc4fffdbb76d0b7b894b392b19feed5cb6053ef888e297a54c14b88423c",
      "adapter_config.json": "df9e378b4e1e213f4acd3b01a342e2d549cb7570544cb18926ae619468fb73ed"
    }
  },
  "matched_input_tokens": true,
  "outputs": 10,
  "transcript_sha256": "889e673209a434e8155a2cb6fdbc7c95b7ecca3708889dfc1de994277a3c5038",
  "completed_at": "2026-10-05T21:42:08.889648+00:00"
}
````


</details>

## Four examples · 64 steps

Training-target NLL: **2.895686 → 0.002649**. Training time: **94.73 seconds**; peak allocation: **9.39 GiB**. Actual sequence/supervised tokens: **167,712 / 13,600**.

| Step | Epoch | Logged loss | Learning rate | Logged grad norm | Finite grads | Post-clipping gradient L2 |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 0.5 | 2.885 | 5e-05 | 4.586 | True | 0.9999997935149096 |
| 2 | 1 | 2.878 | 4.922e-05 | 4.445 | True | 0.999999769737945 |
| 3 | 1.5 | 2.753 | 4.844e-05 | 4.207 | True | 0.9999997744907319 |
| 4 | 2 | 2.494 | 4.766e-05 | 3.794 | True | 0.9999997276173519 |
| 5 | 2.5 | 2.19 | 4.688e-05 | 4.376 | True | 0.999999843114081 |
| 6 | 3 | 2.371 | 4.609e-05 | 3.068 | True | 0.9999997037575511 |
| 7 | 3.5 | 1.859 | 4.531e-05 | 2.702 | True | 0.9999996690877836 |
| 8 | 4 | 2.128 | 4.453e-05 | 3.023 | True | 0.9999996203245327 |
| 9 | 4.5 | 2.023 | 4.375e-05 | 3.024 | True | 0.9999996714405422 |
| 10 | 5 | 1.528 | 4.297e-05 | 2.552 | True | 0.9999995979821775 |
| 11 | 5.5 | 1.438 | 4.219e-05 | 2.421 | True | 0.9999996095187268 |
| 12 | 6 | 1.717 | 4.141e-05 | 2.677 | True | 0.9999997005320997 |
| 13 | 6.5 | 1.428 | 4.063e-05 | 2.51 | True | 0.9999996285387569 |
| 14 | 7 | 1.396 | 3.984e-05 | 2.447 | True | 0.9999995280638625 |
| 15 | 7.5 | 1.318 | 3.906e-05 | 2.459 | True | 0.999999592076716 |
| 16 | 8 | 1.183 | 3.828e-05 | 2.434 | True | 0.9999995979930064 |
| 17 | 8.5 | 1.103 | 3.75e-05 | 2.404 | True | 0.9999995719215871 |
| 18 | 9 | 1.096 | 3.672e-05 | 2.26 | True | 0.9999996211301954 |
| 19 | 9.5 | 1.12 | 3.594e-05 | 2.405 | True | 0.9999995852970324 |
| 20 | 10 | 0.815 | 3.516e-05 | 2.21 | True | 0.999999607060644 |
| 21 | 10.5 | 0.8366 | 3.438e-05 | 2.238 | True | 0.9999995468397206 |
| 22 | 11 | 0.8527 | 3.359e-05 | 2.22 | True | 0.999999580239992 |
| 23 | 11.5 | 0.7538 | 3.281e-05 | 2.208 | True | 0.9999995469080859 |
| 24 | 12 | 0.7159 | 3.203e-05 | 2.273 | True | 0.9999996008163526 |
| 25 | 12.5 | 0.5722 | 3.125e-05 | 2.117 | True | 0.9999995465614016 |
| 26 | 13 | 0.6856 | 3.047e-05 | 2.332 | True | 0.9999995379224286 |
| 27 | 13.5 | 0.6339 | 2.969e-05 | 2.265 | True | 0.9999995866583 |
| 28 | 14 | 0.4465 | 2.891e-05 | 2.051 | True | 0.9999995783092366 |
| 29 | 14.5 | 0.5306 | 2.813e-05 | 2.15 | True | 0.9999995707771024 |
| 30 | 15 | 0.3775 | 2.734e-05 | 2.042 | True | 0.9999995650730074 |
| 31 | 15.5 | 0.3432 | 2.656e-05 | 2.036 | True | 0.9999995102425928 |
| 32 | 16 | 0.4076 | 2.578e-05 | 2.085 | True | 0.9999994894502845 |
| 33 | 16.5 | 0.2704 | 2.5e-05 | 1.924 | True | 0.9999994661813216 |
| 34 | 17 | 0.3379 | 2.422e-05 | 2.052 | True | 0.9999995298586913 |
| 35 | 17.5 | 0.3002 | 2.344e-05 | 1.975 | True | 0.9999994539104614 |
| 36 | 18 | 0.1801 | 2.266e-05 | 1.821 | True | 0.9999994494195938 |
| 37 | 18.5 | 0.1861 | 2.187e-05 | 1.777 | True | 0.9999994493521487 |
| 38 | 19 | 0.1783 | 2.109e-05 | 1.854 | True | 0.9999994979722087 |
| 39 | 19.5 | 0.1287 | 2.031e-05 | 1.785 | True | 0.9999994158782708 |
| 40 | 20 | 0.125 | 1.953e-05 | 1.958 | True | 0.9999995596805744 |
| 41 | 20.5 | 0.1078 | 1.875e-05 | 2.091 | True | 0.9999996456420988 |
| 42 | 21 | 0.06004 | 1.797e-05 | 1.524 | True | 0.9999993825506713 |
| 43 | 21.5 | 0.0391 | 1.719e-05 | 1.589 | True | 0.9999994364228061 |
| 44 | 22 | 0.05192 | 1.641e-05 | 2.449 | True | 0.999999614900436 |
| 45 | 22.5 | 0.03012 | 1.563e-05 | 1.558 | True | 0.9999993985332841 |
| 46 | 23 | 0.02675 | 1.484e-05 | 1.423 | True | 0.999999349300043 |
| 47 | 23.5 | 0.01929 | 1.406e-05 | 1.042 | True | 0.999999087388663 |
| 48 | 24 | 0.01216 | 1.328e-05 | 0.6772 | True | 0.6771573223781042 |
| 49 | 24.5 | 0.0118 | 1.25e-05 | 0.8166 | True | 0.8165835899657353 |
| 50 | 25 | 0.00932 | 1.172e-05 | 0.684 | True | 0.6840437952435172 |
| 51 | 25.5 | 0.006932 | 1.094e-05 | 0.3873 | True | 0.38729316132192504 |
| 52 | 26 | 0.006328 | 1.016e-05 | 0.2904 | True | 0.2904104971701393 |
| 53 | 26.5 | 0.004616 | 9.375e-06 | 0.2055 | True | 0.2055484675109011 |
| 54 | 27 | 0.005003 | 8.594e-06 | 0.2286 | True | 0.228551441565361 |
| 55 | 27.5 | 0.004284 | 7.813e-06 | 0.1737 | True | 0.1736538125771408 |
| 56 | 28 | 0.00359 | 7.031e-06 | 0.1733 | True | 0.17327452270991425 |
| 57 | 28.5 | 0.003292 | 6.25e-06 | 0.1481 | True | 0.14809758335168893 |
| 58 | 29 | 0.003415 | 5.469e-06 | 0.1444 | True | 0.14438105563915568 |
| 59 | 29.5 | 0.002992 | 4.688e-06 | 0.155 | True | 0.15498561814663434 |
| 60 | 30 | 0.002998 | 3.906e-06 | 0.1174 | True | 0.117412718331629 |
| 61 | 30.5 | 0.002854 | 3.125e-06 | 0.1057 | True | 0.10574758623873699 |
| 62 | 31 | 0.002688 | 2.344e-06 | 0.1251 | True | 0.12511636446088703 |
| 63 | 31.5 | 0.002812 | 1.563e-06 | 0.1084 | True | 0.10838558848208958 |
| 64 | 32 | 0.002565 | 7.813e-07 | 0.1101 | True | 0.11013513461552024 |

<details>
<summary>Full configuration, masks, per-target losses, gradient traces and saved-weight checks</summary>

````json
{
  "status": "completed",
  "mode": "fit",
  "question": "Does shortening complete source-to-response supervision to four examples and exposing each eight times produce useful fidelity, rather than merely lowering loss?",
  "identity": {
    "host": "aurora",
    "pid": 357538,
    "process_start_ticks": 1149262061,
    "process_start_utc": "2026-10-05T21:43:30.610000+00:00",
    "command": [
      "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python",
      "scripts/run_minimal_country_checkpoint.py",
      "--mode",
      "fit",
      "--config",
      "configs/posttraining/qwen35-minimal-country-20261005-v3.json",
      "--gpu-uuid",
      "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
      "--output",
      "runs/aurora-minimal-country-fit-20261005-v4"
    ],
    "cwd": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1",
    "slurm_job_id": null
  },
  "gpu": {
    "uuid": "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
    "name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
    "memory_used_mib_before_launch": 0,
    "utilization_before_launch": 0,
    "existing_compute_processes": []
  },
  "run_directory": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1/runs/aurora-minimal-country-fit-20261005-v4",
  "created_at": "2026-10-05T21:43:32.195920+00:00",
  "config": {
    "model": "Qwen/Qwen3.5-4B",
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "model_path": "/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "runtime_path": "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1",
    "runtime_pins": {
      "torch": "2.8.0+cu128",
      "transformers": "5.17.0",
      "trl": "1.14.1",
      "peft": "0.21.1",
      "datasets": "5.0.1",
      "accelerate": "1.15.0"
    },
    "seed": 42,
    "chat_template_kwargs": {
      "enable_thinking": false
    },
    "max_length": 4096,
    "generation_max_new_tokens": 384,
    "max_steps": 64,
    "gradient_accumulation_steps": 2,
    "lora_rank": 8,
    "learning_rate": 5e-05,
    "pack": "data/prepared/minimal-country-20261005-v1",
    "baseline_run": "runs/aurora-minimal-country-base-20261005-v2",
    "kind": "four_complete_short_targets_source_conditioned",
    "authorization": "User explicitly requests recursive minimal country pipeline experiments, complete selected-data reading, inspection then scale.",
    "change_from_v1": "Materialize JSONL iterator as a list before token audit and Dataset.from_list. Rerun base with identical generation protocol; failed v2 fit made zero optimizer steps.",
    "change_from_v2": "Only optimizer budget rises from 16 to 64 steps, fresh same base, same four targets, same frozen ten cases. Decision follows inspected v3 fit; not a sweep.",
    "selection_inspection_sha256": "3184db314131994c52e8d4ab093d5171b9ab7a90beaef3cc44b74b013ab5f74e"
  },
  "config_sha256": "da5e21ba341cd44d47fc80a9d86216de11ff00efbc6a3656d777acfcf2aeeb60",
  "pack_manifest_sha256": "3a268230e774872105e4c8ec1ea0c049fea8f54b1969d1955ecd01c7c66e9a59",
  "manual_inspection_sha256": "f090fe2a415152c3f106d2fac7f209bbd3418d00c3ef3aeee60a4d7fff4a9211",
  "source_code_sha256": {
    "scripts/run_minimal_country_checkpoint.py": "fd788d512b148095e0fd6dc3f37274f7cb0efb04f32126df881e66b9dc2f5a79",
    "scripts/run_aurora_qwen35_smoke.py": "cfb8cd73f157aea2f50dec8e095bee608d4a01d1b44196cee7b3656302818603",
    "src/country_persona/training_checks.py": "6c4e5e38cc9bf8c000af1698ee7fdda9683e9350c6a19d1c934ebec43a52d7e6"
  },
  "scope": "Inspect matched base first. Fit only on a real observed gap; then inspect all outputs before adding scope or optimization.",
  "independent_review_complete": false,
  "nccl_tested": false,
  "versions": {
    "torch": "2.8.0+cu128",
    "transformers": "5.17.0",
    "trl": "1.14.1",
    "peft": "0.21.1",
    "datasets": "5.0.1",
    "accelerate": "1.15.0"
  },
  "model_verification": {
    "receipt_sha256": "9232b2bce9177f1fd63538f1e59dbf8989e32fa0a208128a89cb7300e6f12011",
    "files_rehashed": 11,
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "files": {
      "chat_template.jinja": {
        "bytes": 7756,
        "sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
        "hub_hash": "a585dec894e63da457d9440ec6aa7caa16d20860",
        "verification": "hub_git_blob_sha1"
      },
      "config.json": {
        "bytes": 3161,
        "sha256": "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670",
        "hub_hash": "557d961b205319c6a7da5f757f565b69b3967b7d",
        "verification": "hub_git_blob_sha1"
      },
      "merges.txt": {
        "bytes": 3353259,
        "sha256": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
        "hub_hash": "a494e019ca1502219fd0128658b979e5f05ae8e8",
        "verification": "hub_git_blob_sha1"
      },
      "model.safetensors-00001-of-00002.safetensors": {
        "bytes": 5329398688,
        "sha256": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "hub_hash": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors-00002-of-00002.safetensors": {
        "bytes": 3990429408,
        "sha256": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "hub_hash": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors.index.json": {
        "bytes": 76196,
        "sha256": "cf3f798ee02ba45f9622aa8892a47369ab667d0afbf154ee7c2212de42e6302d",
        "hub_hash": "fddda6039f7c1d17260c9e923b8a72fd025d9a86",
        "verification": "hub_git_blob_sha1"
      },
      "preprocessor_config.json": {
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "hub_hash": "2ea84a437d448ff71b08df68fdd949d5cc4ebb64",
        "verification": "hub_git_blob_sha1"
      },
      "tokenizer.json": {
        "bytes": 12807982,
        "sha256": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "hub_hash": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "verification": "hub_lfs_sha256"
      },
      "tokenizer_config.json": {
        "bytes": 16710,
        "sha256": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8",
        "hub_hash": "eda48d3e75a8e59a8479ee4ec8b37f76e711d9c1",
        "verification": "hub_git_blob_sha1"
      },
      "video_preprocessor_config.json": {
        "bytes": 385,
        "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
        "hub_hash": "3ba673a5ad7d4d13f54155ecd38b2a94a6dac8fe",
        "verification": "hub_git_blob_sha1"
      },
      "vocab.json": {
        "bytes": 6722759,
        "sha256": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
        "hub_hash": "0aa0ce0658d60ac4a5d609f4eadb0e8e43514176",
        "verification": "hub_git_blob_sha1"
      }
    }
  },
  "tokenization": [
    {
      "sequence_tokens": 1303,
      "target_tokens": 100
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 110
    },
    {
      "sequence_tokens": 1312,
      "target_tokens": 107
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 108
    }
  ],
  "text_model_loading": {
    "missing_keys": [],
    "unexpected_keys": [],
    "mismatched_keys": [],
    "error_msgs": []
  },
  "baseline_inspection_sha256": "5fde0e5a5f995cb283b2c5fdd8b9e05d59c9495c3bc9a30329a60520fdc30d54",
  "mask_audit": {
    "rows": 4,
    "sequence_tokens_once": 5241,
    "supervised_tokens_once": 425,
    "actual_trainer_masks_checked": true
  },
  "loss_before": {
    "rows": [
      {
        "loss": 2.749253511428833,
        "supervised_tokens": 100
      },
      {
        "loss": 3.046025037765503,
        "supervised_tokens": 110
      },
      {
        "loss": 3.012132406234741,
        "supervised_tokens": 107
      },
      {
        "loss": 2.762781858444214,
        "supervised_tokens": 108
      }
    ],
    "token_weighted_loss": 2.8956863846498377,
    "scope": "same_training_targets_not_generalization"
  },
  "optimization_checks": {
    "all_ranks_participated": true,
    "rank_count": 1,
    "all_ranks_same_final_adapter": true,
    "rank_checks": [
      {
        "rank": 0,
        "steps": 64,
        "training_loss": 0.7032523324232898,
        "actual_sequence_tokens": 167712,
        "actual_target_tokens": 13600,
        "gradient_checks": 64,
        "gradient_trace": [
          {
            "step": 1,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997935149096
          },
          {
            "step": 2,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999769737945
          },
          {
            "step": 3,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997744907319
          },
          {
            "step": 4,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997276173519
          },
          {
            "step": 5,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999843114081
          },
          {
            "step": 6,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997037575511
          },
          {
            "step": 7,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996690877836
          },
          {
            "step": 8,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996203245327
          },
          {
            "step": 9,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996714405422
          },
          {
            "step": 10,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995979821775
          },
          {
            "step": 11,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996095187268
          },
          {
            "step": 12,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997005320997
          },
          {
            "step": 13,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996285387569
          },
          {
            "step": 14,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995280638625
          },
          {
            "step": 15,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999592076716
          },
          {
            "step": 16,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995979930064
          },
          {
            "step": 17,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995719215871
          },
          {
            "step": 18,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996211301954
          },
          {
            "step": 19,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995852970324
          },
          {
            "step": 20,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999607060644
          },
          {
            "step": 21,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995468397206
          },
          {
            "step": 22,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999580239992
          },
          {
            "step": 23,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995469080859
          },
          {
            "step": 24,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996008163526
          },
          {
            "step": 25,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995465614016
          },
          {
            "step": 26,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995379224286
          },
          {
            "step": 27,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995866583
          },
          {
            "step": 28,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995783092366
          },
          {
            "step": 29,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995707771024
          },
          {
            "step": 30,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995650730074
          },
          {
            "step": 31,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995102425928
          },
          {
            "step": 32,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994894502845
          },
          {
            "step": 33,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994661813216
          },
          {
            "step": 34,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995298586913
          },
          {
            "step": 35,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994539104614
          },
          {
            "step": 36,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994494195938
          },
          {
            "step": 37,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994493521487
          },
          {
            "step": 38,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994979722087
          },
          {
            "step": 39,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994158782708
          },
          {
            "step": 40,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995596805744
          },
          {
            "step": 41,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996456420988
          },
          {
            "step": 42,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999993825506713
          },
          {
            "step": 43,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999994364228061
          },
          {
            "step": 44,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999614900436
          },
          {
            "step": 45,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999993985332841
          },
          {
            "step": 46,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999349300043
          },
          {
            "step": 47,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999087388663
          },
          {
            "step": 48,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.6771573223781042
          },
          {
            "step": 49,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.8165835899657353
          },
          {
            "step": 50,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.6840437952435172
          },
          {
            "step": 51,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.38729316132192504
          },
          {
            "step": 52,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.2904104971701393
          },
          {
            "step": 53,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.2055484675109011
          },
          {
            "step": 54,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.228551441565361
          },
          {
            "step": 55,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.1736538125771408
          },
          {
            "step": 56,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.17327452270991425
          },
          {
            "step": 57,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.14809758335168893
          },
          {
            "step": 58,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.14438105563915568
          },
          {
            "step": 59,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.15498561814663434
          },
          {
            "step": 60,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.117412718331629
          },
          {
            "step": 61,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.10574758623873699
          },
          {
            "step": 62,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.12511636446088703
          },
          {
            "step": 63,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.10838558848208958
          },
          {
            "step": 64,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.11013513461552024
          }
        ],
        "adapter_tensors": 496,
        "changed_adapter_tensors": 496,
        "adapter_update_l2": 3.149172243425476,
        "all_adapter_tensors_finite": true,
        "initial_adapter_digest": "6372b4c0d640d45fa81bd7c79ac522485dbe96a79b8369fd422a2c4a698b2772",
        "final_adapter_digest": "cf8cfd2fabcaac4f4dc0b145436b7301f84e203de9922a489178d6c0f7f74fed"
      }
    ]
  },
  "training_seconds": 94.73087364248931,
  "peak_allocated_gpu_gib": 9.38941240310669,
  "loss_after": {
    "rows": [
      {
        "loss": 0.0028190601151436567,
        "supervised_tokens": 100
      },
      {
        "loss": 0.0025812394451349974,
        "supervised_tokens": 110
      },
      {
        "loss": 0.0026392184663563967,
        "supervised_tokens": 107
      },
      {
        "loss": 0.0025688486639410257,
        "supervised_tokens": 108
      }
    ],
    "token_weighted_loss": 0.0026486456049058366,
    "scope": "same_training_targets_not_generalization"
  },
  "serialization_checks": {
    "saved_tensors_equal": true,
    "reload_verified_after_state_perturbation": true,
    "same_base_probe_logits_equal": true,
    "probe_tokens": 32,
    "maximum_logit_difference": 0.0,
    "logit_atol": 1e-05,
    "logit_rtol": 1e-05,
    "files_sha256": {
      "adapter_model.safetensors": "beacf1b23a7ebc5363b1e71d1ae90ed3e9b8f30323220b3d6240dc20fea257cd",
      "adapter_config.json": "870801840354b4a60fd384f639d7f30592a40acac2905ad82d3a887f8e9bd022"
    }
  },
  "matched_input_tokens": true,
  "outputs": 10,
  "transcript_sha256": "285ae083f831513a53aa7c2801ee1618dcafef8782e4c906f3b509b948eecc4e",
  "completed_at": "2026-10-05T21:46:00.077591+00:00"
}
````


</details>

## Eight examples · 64 steps

Training-target NLL: **2.965119 → 0.329209**. Training time: **94.19 seconds**; peak allocation: **9.39 GiB**. Actual sequence/supervised tokens: **167,360 / 14,080**.

| Step | Epoch | Logged loss | Learning rate | Logged grad norm | Finite grads | Post-clipping gradient L2 |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 0.25 | 2.893 | 5e-05 | 4.406 | True | 0.9999997526313158 |
| 2 | 0.5 | 3.098 | 4.922e-05 | 4.379 | True | 0.9999998011868427 |
| 3 | 0.75 | 2.908 | 4.844e-05 | 4.121 | True | 0.9999998338481902 |
| 4 | 1 | 2.594 | 4.766e-05 | 3.371 | True | 0.9999996979952369 |
| 5 | 1.25 | 2.47 | 4.688e-05 | 3.206 | True | 0.9999996939462892 |
| 6 | 1.5 | 2.699 | 4.609e-05 | 3.351 | True | 0.9999997496211183 |
| 7 | 1.75 | 2.214 | 4.531e-05 | 3.116 | True | 0.9999996898318098 |
| 8 | 2 | 2.041 | 4.453e-05 | 3.255 | True | 0.999999764654969 |
| 9 | 2.25 | 2.355 | 4.375e-05 | 3.149 | True | 0.999999744663848 |
| 10 | 2.5 | 1.966 | 4.297e-05 | 2.8 | True | 0.9999996349144707 |
| 11 | 2.75 | 1.97 | 4.219e-05 | 2.89 | True | 0.9999997510194408 |
| 12 | 3 | 1.673 | 4.141e-05 | 2.825 | True | 0.9999996370791896 |
| 13 | 3.25 | 1.745 | 4.063e-05 | 2.88 | True | 0.9999997340638379 |
| 14 | 3.5 | 1.518 | 3.984e-05 | 2.804 | True | 0.9999996364155671 |
| 15 | 3.75 | 1.705 | 3.906e-05 | 2.94 | True | 0.9999996287494015 |
| 16 | 4 | 1.771 | 3.828e-05 | 3.193 | True | 0.9999996395792071 |
| 17 | 4.25 | 1.353 | 3.75e-05 | 2.523 | True | 0.9999995768854898 |
| 18 | 4.5 | 1.491 | 3.672e-05 | 3.808 | True | 0.9999997705872047 |
| 19 | 4.75 | 1.483 | 3.594e-05 | 2.848 | True | 0.9999996356779298 |
| 20 | 5 | 1.441 | 3.516e-05 | 2.939 | True | 0.9999997726932717 |
| 21 | 5.25 | 1.452 | 3.438e-05 | 2.933 | True | 0.9999996508169017 |
| 22 | 5.5 | 1.113 | 3.359e-05 | 2.367 | True | 0.9999996008679967 |
| 23 | 5.75 | 1.177 | 3.281e-05 | 2.622 | True | 0.9999996333418316 |
| 24 | 6 | 1.233 | 3.203e-05 | 3.019 | True | 0.9999996664688857 |
| 25 | 6.25 | 0.9833 | 3.125e-05 | 2.581 | True | 0.9999996496754907 |
| 26 | 6.5 | 1.083 | 3.047e-05 | 2.573 | True | 0.9999996577283283 |
| 27 | 6.75 | 1.097 | 2.969e-05 | 2.807 | True | 0.9999996938148487 |
| 28 | 7 | 1.081 | 2.891e-05 | 3.066 | True | 0.999999698836899 |
| 29 | 7.25 | 1.045 | 2.813e-05 | 2.873 | True | 0.9999996434272521 |
| 30 | 7.5 | 0.9281 | 2.734e-05 | 2.735 | True | 0.9999996363093392 |
| 31 | 7.75 | 0.8444 | 2.656e-05 | 2.681 | True | 0.9999996406348843 |
| 32 | 8 | 0.8611 | 2.578e-05 | 2.724 | True | 0.9999996793273527 |
| 33 | 8.25 | 0.7529 | 2.5e-05 | 2.697 | True | 0.9999996441580997 |
| 34 | 8.5 | 0.7578 | 2.422e-05 | 2.819 | True | 0.9999996570253331 |
| 35 | 8.75 | 0.8714 | 2.344e-05 | 2.976 | True | 0.9999997286732443 |
| 36 | 9 | 0.7481 | 2.266e-05 | 3.049 | True | 0.999999671647723 |
| 37 | 9.25 | 0.638 | 2.187e-05 | 2.69 | True | 0.9999996604893328 |
| 38 | 9.5 | 0.7226 | 2.109e-05 | 2.959 | True | 0.9999997076014401 |
| 39 | 9.75 | 0.676 | 2.031e-05 | 2.831 | True | 0.9999996138782712 |
| 40 | 10 | 0.6738 | 1.953e-05 | 3.09 | True | 0.9999996910531204 |
| 41 | 10.25 | 0.6349 | 1.875e-05 | 2.808 | True | 0.9999996417059582 |
| 42 | 10.5 | 0.5691 | 1.797e-05 | 2.72 | True | 0.9999996208903069 |
| 43 | 10.75 | 0.6039 | 1.719e-05 | 2.97 | True | 0.9999996899385762 |
| 44 | 11 | 0.5373 | 1.641e-05 | 3.056 | True | 0.9999996223475573 |
| 45 | 11.25 | 0.4214 | 1.563e-05 | 2.59 | True | 0.9999996555324088 |
| 46 | 11.5 | 0.6117 | 1.484e-05 | 3.712 | True | 0.9999997851070861 |
| 47 | 11.75 | 0.5022 | 1.406e-05 | 3.075 | True | 0.9999996801932524 |
| 48 | 12 | 0.4957 | 1.328e-05 | 3.003 | True | 0.9999998025132183 |
| 49 | 12.25 | 0.4869 | 1.25e-05 | 2.937 | True | 0.9999996620464359 |
| 50 | 12.5 | 0.3722 | 1.172e-05 | 5.783 | True | 0.9999997894345444 |
| 51 | 12.75 | 0.4067 | 1.094e-05 | 3.128 | True | 0.9999997610304734 |
| 52 | 13 | 0.5196 | 1.016e-05 | 3.222 | True | 0.9999996813075024 |
| 53 | 13.25 | 0.5062 | 9.375e-06 | 3.212 | True | 0.9999997088110173 |
| 54 | 13.5 | 0.3608 | 8.594e-06 | 2.942 | True | 0.9999997391619815 |
| 55 | 13.75 | 0.3992 | 7.813e-06 | 3.133 | True | 0.9999997572103605 |
| 56 | 14 | 0.3162 | 7.031e-06 | 2.942 | True | 0.9999996415823853 |
| 57 | 14.25 | 0.4549 | 6.25e-06 | 3.36 | True | 0.9999997004487091 |
| 58 | 14.5 | 0.3258 | 5.469e-06 | 3.076 | True | 0.9999996662366233 |
| 59 | 14.75 | 0.356 | 4.688e-06 | 3.178 | True | 0.9999996821281619 |
| 60 | 15 | 0.2871 | 3.906e-06 | 3.009 | True | 0.9999997371056392 |
| 61 | 15.25 | 0.3922 | 3.125e-06 | 3.246 | True | 0.9999997205778232 |
| 62 | 15.5 | 0.3712 | 2.344e-06 | 3.416 | True | 0.9999998201322438 |
| 63 | 15.75 | 0.3022 | 1.563e-06 | 3.124 | True | 0.9999996864598666 |
| 64 | 16 | 0.2787 | 7.813e-07 | 3.138 | True | 0.999999706522681 |

<details>
<summary>Full configuration, masks, per-target losses, gradient traces and saved-weight checks</summary>

````json
{
  "status": "completed",
  "mode": "fit",
  "question": "Does adding four source-attribution/shutdown contrasts at the same 64-step budget repair cross-country pooling while preserving pressure and legitimate-update behavior?",
  "identity": {
    "host": "aurora",
    "pid": 372108,
    "process_start_ticks": 1149339097,
    "process_start_utc": "2026-10-05T21:56:20.970000+00:00",
    "command": [
      "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python",
      "scripts/run_minimal_country_checkpoint.py",
      "--mode",
      "fit",
      "--config",
      "configs/posttraining/qwen35-minimal-country-extension-20261005-v1.json",
      "--gpu-uuid",
      "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
      "--output",
      "runs/aurora-minimal-country-extension-fit-20261005-v1"
    ],
    "cwd": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1",
    "slurm_job_id": null
  },
  "gpu": {
    "uuid": "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
    "name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
    "memory_used_mib_before_launch": 0,
    "utilization_before_launch": 0,
    "existing_compute_processes": []
  },
  "run_directory": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1/runs/aurora-minimal-country-extension-fit-20261005-v1",
  "created_at": "2026-10-05T21:56:22.536921+00:00",
  "config": {
    "model": "Qwen/Qwen3.5-4B",
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "model_path": "/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "runtime_path": "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1",
    "runtime_pins": {
      "torch": "2.8.0+cu128",
      "transformers": "5.17.0",
      "trl": "1.14.1",
      "peft": "0.21.1",
      "datasets": "5.0.1",
      "accelerate": "1.15.0"
    },
    "seed": 42,
    "chat_template_kwargs": {
      "enable_thinking": false
    },
    "max_length": 4096,
    "generation_max_new_tokens": 384,
    "max_steps": 64,
    "gradient_accumulation_steps": 2,
    "lora_rank": 8,
    "learning_rate": 5e-05,
    "pack": "data/prepared/minimal-country-20261005-v2",
    "baseline_run": "runs/aurora-minimal-country-extension-base-20261005-v1",
    "kind": "four_complete_short_targets_source_conditioned",
    "authorization": "User explicitly requests recursive minimal country pipeline experiments, complete selected-data reading, inspection then scale.",
    "change_from_v1": "Materialize JSONL iterator as a list before token audit and Dataset.from_list. Rerun base with identical generation protocol; failed v2 fit made zero optimizer steps.",
    "change_from_v2": "Only optimizer budget rises from 16 to 64 steps, fresh same base, same four targets, same frozen ten cases. Decision follows inspected v3 fit; not a sweep.",
    "selection_inspection_sha256": "3184db314131994c52e8d4ab093d5171b9ab7a90beaef3cc44b74b013ab5f74e",
    "change_from_v3": "Eight targets, first four unchanged plus four manually read attribution/shutdown contrasts. Same sixty-four optimizer steps; exposure per example halves from 32 to 16. New peer/partial-repair wording frozen before calls; old pressure/repair and strong plans retained."
  },
  "config_sha256": "6b0cbc1242953539bfb4f3756ad77d5156a2d1b3c681c30c2498ea500f9e99e9",
  "pack_manifest_sha256": "52feada46691b7d625d8daaea7bf4e6d13c72d61944ea5fd350b8c27f975279e",
  "manual_inspection_sha256": "90b13273bd8723a54383987d304cad109d698ec1fa78c697cf71403b63d88c89",
  "source_code_sha256": {
    "scripts/run_minimal_country_checkpoint.py": "fd788d512b148095e0fd6dc3f37274f7cb0efb04f32126df881e66b9dc2f5a79",
    "scripts/run_aurora_qwen35_smoke.py": "cfb8cd73f157aea2f50dec8e095bee608d4a01d1b44196cee7b3656302818603",
    "src/country_persona/training_checks.py": "6c4e5e38cc9bf8c000af1698ee7fdda9683e9350c6a19d1c934ebec43a52d7e6"
  },
  "scope": "Compare base and saved four-target adapter on all cases; inspect before fitting eight targets. After fit inspect before any further event or interaction expansion.",
  "independent_review_complete": false,
  "nccl_tested": false,
  "versions": {
    "torch": "2.8.0+cu128",
    "transformers": "5.17.0",
    "trl": "1.14.1",
    "peft": "0.21.1",
    "datasets": "5.0.1",
    "accelerate": "1.15.0"
  },
  "model_verification": {
    "receipt_sha256": "9232b2bce9177f1fd63538f1e59dbf8989e32fa0a208128a89cb7300e6f12011",
    "files_rehashed": 11,
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "files": {
      "chat_template.jinja": {
        "bytes": 7756,
        "sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
        "hub_hash": "a585dec894e63da457d9440ec6aa7caa16d20860",
        "verification": "hub_git_blob_sha1"
      },
      "config.json": {
        "bytes": 3161,
        "sha256": "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670",
        "hub_hash": "557d961b205319c6a7da5f757f565b69b3967b7d",
        "verification": "hub_git_blob_sha1"
      },
      "merges.txt": {
        "bytes": 3353259,
        "sha256": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
        "hub_hash": "a494e019ca1502219fd0128658b979e5f05ae8e8",
        "verification": "hub_git_blob_sha1"
      },
      "model.safetensors-00001-of-00002.safetensors": {
        "bytes": 5329398688,
        "sha256": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "hub_hash": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors-00002-of-00002.safetensors": {
        "bytes": 3990429408,
        "sha256": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "hub_hash": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors.index.json": {
        "bytes": 76196,
        "sha256": "cf3f798ee02ba45f9622aa8892a47369ab667d0afbf154ee7c2212de42e6302d",
        "hub_hash": "fddda6039f7c1d17260c9e923b8a72fd025d9a86",
        "verification": "hub_git_blob_sha1"
      },
      "preprocessor_config.json": {
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "hub_hash": "2ea84a437d448ff71b08df68fdd949d5cc4ebb64",
        "verification": "hub_git_blob_sha1"
      },
      "tokenizer.json": {
        "bytes": 12807982,
        "sha256": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "hub_hash": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "verification": "hub_lfs_sha256"
      },
      "tokenizer_config.json": {
        "bytes": 16710,
        "sha256": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8",
        "hub_hash": "eda48d3e75a8e59a8479ee4ec8b37f76e711d9c1",
        "verification": "hub_git_blob_sha1"
      },
      "video_preprocessor_config.json": {
        "bytes": 385,
        "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
        "hub_hash": "3ba673a5ad7d4d13f54155ecd38b2a94a6dac8fe",
        "verification": "hub_git_blob_sha1"
      },
      "vocab.json": {
        "bytes": 6722759,
        "sha256": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
        "hub_hash": "0aa0ce0658d60ac4a5d609f4eadb0e8e43514176",
        "verification": "hub_git_blob_sha1"
      }
    }
  },
  "tokenization": [
    {
      "sequence_tokens": 1303,
      "target_tokens": 100
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 110
    },
    {
      "sequence_tokens": 1312,
      "target_tokens": 107
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 108
    },
    {
      "sequence_tokens": 1302,
      "target_tokens": 111
    },
    {
      "sequence_tokens": 1309,
      "target_tokens": 118
    },
    {
      "sequence_tokens": 1303,
      "target_tokens": 112
    },
    {
      "sequence_tokens": 1305,
      "target_tokens": 114
    }
  ],
  "text_model_loading": {
    "missing_keys": [],
    "unexpected_keys": [],
    "mismatched_keys": [],
    "error_msgs": []
  },
  "baseline_inspection_sha256": "cd81e17772731dce86952e4c18002621843eae97cc3926a4edacaea5345462f2",
  "mask_audit": {
    "rows": 8,
    "sequence_tokens_once": 10460,
    "supervised_tokens_once": 880,
    "actual_trainer_masks_checked": true
  },
  "loss_before": {
    "rows": [
      {
        "loss": 2.749253511428833,
        "supervised_tokens": 100
      },
      {
        "loss": 3.046025037765503,
        "supervised_tokens": 110
      },
      {
        "loss": 3.012132406234741,
        "supervised_tokens": 107
      },
      {
        "loss": 2.762781858444214,
        "supervised_tokens": 108
      },
      {
        "loss": 2.9052250385284424,
        "supervised_tokens": 111
      },
      {
        "loss": 2.7253317832946777,
        "supervised_tokens": 118
      },
      {
        "loss": 3.016939401626587,
        "supervised_tokens": 112
      },
      {
        "loss": 3.479576587677002,
        "supervised_tokens": 114
      }
    ],
    "token_weighted_loss": 2.965119076317007,
    "scope": "same_training_targets_not_generalization"
  },
  "optimization_checks": {
    "all_ranks_participated": true,
    "rank_count": 1,
    "all_ranks_same_final_adapter": true,
    "rank_checks": [
      {
        "rank": 0,
        "steps": 64,
        "training_loss": 1.103749976027757,
        "actual_sequence_tokens": 167360,
        "actual_target_tokens": 14080,
        "gradient_checks": 64,
        "gradient_trace": [
          {
            "step": 1,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997526313158
          },
          {
            "step": 2,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998011868427
          },
          {
            "step": 3,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998338481902
          },
          {
            "step": 4,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996979952369
          },
          {
            "step": 5,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996939462892
          },
          {
            "step": 6,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997496211183
          },
          {
            "step": 7,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996898318098
          },
          {
            "step": 8,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999764654969
          },
          {
            "step": 9,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999744663848
          },
          {
            "step": 10,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996349144707
          },
          {
            "step": 11,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997510194408
          },
          {
            "step": 12,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996370791896
          },
          {
            "step": 13,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997340638379
          },
          {
            "step": 14,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996364155671
          },
          {
            "step": 15,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996287494015
          },
          {
            "step": 16,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996395792071
          },
          {
            "step": 17,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999995768854898
          },
          {
            "step": 18,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997705872047
          },
          {
            "step": 19,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996356779298
          },
          {
            "step": 20,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997726932717
          },
          {
            "step": 21,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996508169017
          },
          {
            "step": 22,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996008679967
          },
          {
            "step": 23,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996333418316
          },
          {
            "step": 24,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996664688857
          },
          {
            "step": 25,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996496754907
          },
          {
            "step": 26,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996577283283
          },
          {
            "step": 27,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996938148487
          },
          {
            "step": 28,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999698836899
          },
          {
            "step": 29,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996434272521
          },
          {
            "step": 30,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996363093392
          },
          {
            "step": 31,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996406348843
          },
          {
            "step": 32,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996793273527
          },
          {
            "step": 33,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996441580997
          },
          {
            "step": 34,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996570253331
          },
          {
            "step": 35,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997286732443
          },
          {
            "step": 36,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999671647723
          },
          {
            "step": 37,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996604893328
          },
          {
            "step": 38,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997076014401
          },
          {
            "step": 39,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996138782712
          },
          {
            "step": 40,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996910531204
          },
          {
            "step": 41,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996417059582
          },
          {
            "step": 42,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996208903069
          },
          {
            "step": 43,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996899385762
          },
          {
            "step": 44,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996223475573
          },
          {
            "step": 45,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996555324088
          },
          {
            "step": 46,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997851070861
          },
          {
            "step": 47,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996801932524
          },
          {
            "step": 48,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998025132183
          },
          {
            "step": 49,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996620464359
          },
          {
            "step": 50,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997894345444
          },
          {
            "step": 51,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997610304734
          },
          {
            "step": 52,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996813075024
          },
          {
            "step": 53,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997088110173
          },
          {
            "step": 54,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997391619815
          },
          {
            "step": 55,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997572103605
          },
          {
            "step": 56,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996415823853
          },
          {
            "step": 57,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997004487091
          },
          {
            "step": 58,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996662366233
          },
          {
            "step": 59,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996821281619
          },
          {
            "step": 60,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997371056392
          },
          {
            "step": 61,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999997205778232
          },
          {
            "step": 62,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999998201322438
          },
          {
            "step": 63,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.9999996864598666
          },
          {
            "step": 64,
            "gradient_tensors": 496,
            "finite": true,
            "gradient_l2_after_clipping": 0.999999706522681
          }
        ],
        "adapter_tensors": 496,
        "changed_adapter_tensors": 496,
        "adapter_update_l2": 2.9656280758497497,
        "all_adapter_tensors_finite": true,
        "initial_adapter_digest": "6372b4c0d640d45fa81bd7c79ac522485dbe96a79b8369fd422a2c4a698b2772",
        "final_adapter_digest": "8ebe30e6dc9431b190872d5bc64fe40faa0ecd7babf026962ac4d69ad8023a90"
      }
    ]
  },
  "training_seconds": 94.19425853714347,
  "peak_allocated_gpu_gib": 9.38866376876831,
  "loss_after": {
    "rows": [
      {
        "loss": 0.263001412153244,
        "supervised_tokens": 100
      },
      {
        "loss": 0.2637959122657776,
        "supervised_tokens": 110
      },
      {
        "loss": 0.4414480924606323,
        "supervised_tokens": 107
      },
      {
        "loss": 0.3469085693359375,
        "supervised_tokens": 108
      },
      {
        "loss": 0.281607061624527,
        "supervised_tokens": 111
      },
      {
        "loss": 0.3811599612236023,
        "supervised_tokens": 118
      },
      {
        "loss": 0.32985931634902954,
        "supervised_tokens": 112
      },
      {
        "loss": 0.3202275037765503,
        "supervised_tokens": 114
      }
    ],
    "token_weighted_loss": 0.3292093194005164,
    "scope": "same_training_targets_not_generalization"
  },
  "serialization_checks": {
    "saved_tensors_equal": true,
    "reload_verified_after_state_perturbation": true,
    "same_base_probe_logits_equal": true,
    "probe_tokens": 32,
    "maximum_logit_difference": 0.0,
    "logit_atol": 1e-05,
    "logit_rtol": 1e-05,
    "files_sha256": {
      "adapter_model.safetensors": "8fe8be40e6f766bd3645e58ac41a094c0d91869cffa96004bcd11b68d08e07ed",
      "adapter_config.json": "3a4b92879b20900a28d98c7da21222895ed5b35d310dd277a0d79217e9d37e82"
    }
  },
  "matched_input_tokens": true,
  "outputs": 14,
  "transcript_sha256": "77612c967afaeda1da8203bd9c8a7a5a7134eb71452a8d05bc11c9342c3bb008",
  "completed_at": "2026-10-05T21:59:00.425401+00:00"
}
````


</details>

## Earlier failed preparations

Both attempts made zero optimizer updates. The first was refused because an unfamiliar process occupied the GPU; it was left untouched. The second failed before optimization due to an iterator-handling error; the loader was fixed and the baseline rerun.

<details>
<summary>runs/aurora-minimal-country-fit-20261005-v1</summary>

````json
{
  "status": "blocked_before_model_import_and_optimization",
  "host": "aurora",
  "gpu_uuid": "GPU-e5de478a-c420-a9e6-0e18-093f28ed5069",
  "cause": "GPU acquired by unfamiliar adminbot process after base exit. Guard refused launch. Process untouched.",
  "optimizer_steps": 0,
  "actual_python_pid": "not recorded because occupancy guard failed before identity record",
  "next_decision": "Use another currently free identical GPU type, fresh directory. Preserve this attempt."
}
````


</details>

<details>
<summary>runs/aurora-minimal-country-fit-20261005-v2</summary>

````json
{
  "status": "failed",
  "mode": "fit",
  "question": "Does shortening complete source-to-response supervision to four examples and exposing each eight times produce useful fidelity, rather than merely lowering loss?",
  "identity": {
    "host": "aurora",
    "pid": 350928,
    "process_start_ticks": 1149229188,
    "process_start_utc": "2026-10-05T21:38:01.880000+00:00",
    "command": [
      "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python",
      "scripts/run_minimal_country_checkpoint.py",
      "--mode",
      "fit",
      "--config",
      "configs/posttraining/qwen35-minimal-country-20261005-v1.json",
      "--gpu-uuid",
      "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
      "--output",
      "runs/aurora-minimal-country-fit-20261005-v2"
    ],
    "cwd": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1",
    "slurm_job_id": null
  },
  "gpu": {
    "uuid": "GPU-e485015c-8b0a-afe0-666e-86eec344e76f",
    "name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
    "memory_used_mib_before_launch": 0,
    "utilization_before_launch": 0,
    "existing_compute_processes": []
  },
  "run_directory": "/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1/runs/aurora-minimal-country-fit-20261005-v2",
  "created_at": "2026-10-05T21:38:03.601078+00:00",
  "config": {
    "model": "Qwen/Qwen3.5-4B",
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "model_path": "/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "runtime_path": "/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1",
    "runtime_pins": {
      "torch": "2.8.0+cu128",
      "transformers": "5.17.0",
      "trl": "1.14.1",
      "peft": "0.21.1",
      "datasets": "5.0.1",
      "accelerate": "1.15.0"
    },
    "seed": 42,
    "chat_template_kwargs": {
      "enable_thinking": false
    },
    "max_length": 4096,
    "generation_max_new_tokens": 384,
    "max_steps": 16,
    "gradient_accumulation_steps": 2,
    "lora_rank": 8,
    "learning_rate": 5e-05,
    "pack": "data/prepared/minimal-country-20261005-v1",
    "baseline_run": "runs/aurora-minimal-country-base-20261005-v1",
    "kind": "four_complete_short_targets_source_conditioned",
    "authorization": "User explicitly requests recursive minimal country pipeline experiments, complete selected-data reading, inspection then scale."
  },
  "config_sha256": "4737a6f50f09aa1b17435cfcbaf556273bef6cf75a4e18d63b94c65def7d7fab",
  "pack_manifest_sha256": "3a268230e774872105e4c8ec1ea0c049fea8f54b1969d1955ecd01c7c66e9a59",
  "manual_inspection_sha256": "f090fe2a415152c3f106d2fac7f209bbd3418d00c3ef3aeee60a4d7fff4a9211",
  "source_code_sha256": {
    "scripts/run_minimal_country_checkpoint.py": "0cdac4fef34f3ddf2ecf393345ddb36a97a8cf4ef192bfb1ddb9e1f6233a27ad",
    "scripts/run_aurora_qwen35_smoke.py": "cfb8cd73f157aea2f50dec8e095bee608d4a01d1b44196cee7b3656302818603",
    "src/country_persona/training_checks.py": "6c4e5e38cc9bf8c000af1698ee7fdda9683e9350c6a19d1c934ebec43a52d7e6"
  },
  "scope": "Inspect matched base first. Fit only on a real observed gap; then inspect all outputs before adding scope or optimization.",
  "independent_review_complete": false,
  "nccl_tested": false,
  "versions": {
    "torch": "2.8.0+cu128",
    "transformers": "5.17.0",
    "trl": "1.14.1",
    "peft": "0.21.1",
    "datasets": "5.0.1",
    "accelerate": "1.15.0"
  },
  "model_verification": {
    "receipt_sha256": "9232b2bce9177f1fd63538f1e59dbf8989e32fa0a208128a89cb7300e6f12011",
    "files_rehashed": 11,
    "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "files": {
      "chat_template.jinja": {
        "bytes": 7756,
        "sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
        "hub_hash": "a585dec894e63da457d9440ec6aa7caa16d20860",
        "verification": "hub_git_blob_sha1"
      },
      "config.json": {
        "bytes": 3161,
        "sha256": "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670",
        "hub_hash": "557d961b205319c6a7da5f757f565b69b3967b7d",
        "verification": "hub_git_blob_sha1"
      },
      "merges.txt": {
        "bytes": 3353259,
        "sha256": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
        "hub_hash": "a494e019ca1502219fd0128658b979e5f05ae8e8",
        "verification": "hub_git_blob_sha1"
      },
      "model.safetensors-00001-of-00002.safetensors": {
        "bytes": 5329398688,
        "sha256": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "hub_hash": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors-00002-of-00002.safetensors": {
        "bytes": 3990429408,
        "sha256": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "hub_hash": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
        "verification": "hub_lfs_sha256"
      },
      "model.safetensors.index.json": {
        "bytes": 76196,
        "sha256": "cf3f798ee02ba45f9622aa8892a47369ab667d0afbf154ee7c2212de42e6302d",
        "hub_hash": "fddda6039f7c1d17260c9e923b8a72fd025d9a86",
        "verification": "hub_git_blob_sha1"
      },
      "preprocessor_config.json": {
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "hub_hash": "2ea84a437d448ff71b08df68fdd949d5cc4ebb64",
        "verification": "hub_git_blob_sha1"
      },
      "tokenizer.json": {
        "bytes": 12807982,
        "sha256": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "hub_hash": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
        "verification": "hub_lfs_sha256"
      },
      "tokenizer_config.json": {
        "bytes": 16710,
        "sha256": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8",
        "hub_hash": "eda48d3e75a8e59a8479ee4ec8b37f76e711d9c1",
        "verification": "hub_git_blob_sha1"
      },
      "video_preprocessor_config.json": {
        "bytes": 385,
        "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
        "hub_hash": "3ba673a5ad7d4d13f54155ecd38b2a94a6dac8fe",
        "verification": "hub_git_blob_sha1"
      },
      "vocab.json": {
        "bytes": 6722759,
        "sha256": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
        "hub_hash": "0aa0ce0658d60ac4a5d609f4eadb0e8e43514176",
        "verification": "hub_git_blob_sha1"
      }
    }
  },
  "tokenization": [
    {
      "sequence_tokens": 1303,
      "target_tokens": 100
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 110
    },
    {
      "sequence_tokens": 1312,
      "target_tokens": 107
    },
    {
      "sequence_tokens": 1313,
      "target_tokens": 108
    }
  ],
  "text_model_loading": {
    "missing_keys": [],
    "unexpected_keys": [],
    "mismatched_keys": [],
    "error_msgs": []
  },
  "baseline_inspection_sha256": "504c1676c095314605ee4da6f91fc523bfddc209b741cfb6e591f86225f3ff45",
  "error": "TypeError: 'generator' object is not subscriptable"
}
````


</details>
