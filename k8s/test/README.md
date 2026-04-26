This overlay is for non-GPU test clusters.

What it changes:
- swaps internal images for public test images
- removes the GPU-only node selector
- runs a fake DCGM metrics endpoint
- deploys the in-cluster `gpu-ingest` receiver
- runs the validator from the checked-in `validator.py`
- keeps `telegraf` on log/event collection rather than `dcgm-exporter` metric scrape

Apply with:
`kubectl kustomize --load-restrictor=LoadRestrictionsNone k8s/test | kubectl apply -f -`

Optional:
- replace the in-cluster ingest URL in `patch-configmap.yaml` with a real external endpoint later
- this overlay is only for non-GPU validation; production GPU clusters should use real `dcgm-exporter -> vmagent`
