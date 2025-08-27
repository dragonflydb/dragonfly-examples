# Example: Dragonfly High Availability with Kubernetes Operator

- This example demonstrates how to set up Dragonfly with high availability using its Kubernetes Operator, as part of our blog post [Keeping Dragonfly Always-On: High Availability Options Explained](https://www.dragonflydb.io/blog/dragonfly-high-availability-options-explained).
- Firstly, make sure your Kubernetes cluster is up and running.
- To install Dragonfly Operator, run the following command:

```bash
$> kubectl apply -f https://raw.githubusercontent.com/dragonflydb/dragonfly-operator/main/manifests/dragonfly-operator.yaml
```

- Use the example YAML file to run a Dragonfly high availability setup (1 primary, 2 replicas):

```bash
$> cd /PATH/TO/dragonfly-examples/high-availability/k8s-operator

$> kubectl apply -f dragonfly-sample.yaml
```
