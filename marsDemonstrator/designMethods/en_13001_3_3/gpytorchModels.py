import gpytorch as gp
import torch
from gpytorch.kernels.scale_kernel import ScaleKernel


class ExactGPModel(gp.models.ExactGP):
    def __init__(self, x, y, likelihood, kernel, mean):
        super().__init__(x, y, likelihood)
        self.mean_module = mean
        self.covar_module = ScaleKernel(kernel)
        self.float()
        likelihood.float()

    def forward(self, x): # pylint: disable=arguments-differ
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return gp.distributions.MultivariateNormal(mean, covar)

    def predict(self, x):
        with torch.no_grad(), gp.settings.memory_efficient(), gp.settings.fast_pred_samples(), gp.settings.fast_pred_var():
            self.float()
            observed_pred = self(x)
            lower, upper = observed_pred.confidence_region()
            return observed_pred.mean.numpy(), lower.numpy(), upper.numpy()

    def load_cache(self, pred_dict, x):
        self.likelihood.noise = 1e-3
        with torch.no_grad(), gp.settings.memory_efficient(), gp.settings.fast_pred_samples(), gp.settings.fast_pred_var(), gp.settings.max_cg_iterations(100):
            self(x[0:1, :].float())
            # x1 = pred_dict["x1"]
            # x2 = pred_dict["x2"]
            # mean = pred_dict["mean"]
            # train_prior = gp.distributions.MultivariateNormal(mean, gp.lazy.LazyEvaluatedKernelTensor(x1, x2, self.covar_module))
            # self.prediction_strategy = gp.models.exact_prediction_strategies.prediction_strategy(self.train_inputs, train_prior, self.train_targets, self.likelihood)

            # self.prediction_strategy._memoize_cache = pred_dict["chached_data"]
            # self.prediction_strategy = pred_dict["pred_strat"]
            # self.predict(x[0:1, :])
            self.prediction_strategy.mean_cache.data = pred_dict["mean_cache_data"]
            self.prediction_strategy.covar_cache.data = pred_dict["covar_cache_data"]
