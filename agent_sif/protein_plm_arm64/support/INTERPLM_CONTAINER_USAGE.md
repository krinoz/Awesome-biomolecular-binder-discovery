# InterPLM in the protein PLM image

InterPLM is installed at `/opt/InterPLM` in `/opt/envs/interplm`. SaProtHub remains in
its original isolated environment. Neither environment is added to `PATH`.

Run offline pretrained SAE feature extraction with:

```bash
/opt/envs/interplm/bin/python /opt/interplm/interplm_run.py \
  --sequence MRWQEMGYIFYPRKLR \
  --model esm2-8m --layer 4 --device cuda \
  --output-dir /work/interplm/example
```

Required read-only mounts:

- `/models/esm2/esm2-8m`: Hugging Face ESM2-8M snapshot.
- `/models/esm2/esm2-650m`: the existing SaProtHub ESM2-650M snapshot.
- `/models/interplm/sae`: normalized InterPLM SAE layers.

The upstream README, examples, training scripts, analysis modules, and dashboard are retained
under `/opt/InterPLM`. Pass local model directories to upstream embedding scripts; network
model downloads are disabled at runtime.
