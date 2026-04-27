This overlay is for non-GPU test clusters.

What it changes:
- swaps internal images for public test images
- removes the GPU-only node selector
- runs a fake DCGM metrics endpoint
- expects a server-side `gpu-ingest` receiver and points to its external endpoint
- runs the validator from the checked-in `validator.py`
- keeps `telegraf` on log/event collection rather than `dcgm-exporter` metric scrape

Apply with:
`kubectl kustomize --load-restrictor=LoadRestrictionsNone client/k8s/test | kubectl apply -f -`

Optional:
- replace the external ingest URL in `patch-configmap.yaml` with the real server-cluster endpoint for your environment
- this overlay is only for non-GPU validation; production GPU clusters should use real `dcgm-exporter -> vmagent`
