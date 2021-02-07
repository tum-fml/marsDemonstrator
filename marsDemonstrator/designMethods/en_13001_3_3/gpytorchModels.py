import gpytorch as gp
import torch
from gpytorch.kernels import GridInterpolationKernel, AdditiveStructureKernel, InducingPointKernel, ProductStructureKernel
from gpytorch.kernels.scale_kernel import ScaleKernel
from gpytorch.models import ApproximateGP, ExactGP
from gpytorch.variational import (CholeskyVariationalDistribution,
                                  VariationalStrategy, OrthogonallyDecoupledVariationalStrategy, DeltaVariationalDistribution)
from sklearn.cluster import MiniBatchKMeans
import time


class SVGPModel(ApproximateGP):
    def __init__(self, num_z, kernel, mean, x=None):
        if x is not None:
            k_means = MiniBatchKMeans(num_z)
            k_means = k_means.fit(x)
            z = torch.from_numpy(k_means.cluster_centers_)
        else: 
            z = torch.zeros((num_z, 17))

        variational_distribution = CholeskyVariationalDistribution(z.size(0))
        variational_strategy = VariationalStrategy(self, z, variational_distribution, 
                                                   learn_inducing_locations=True)
        # covar_variational_strategy = VariationalStrategy(self, z, CholeskyVariationalDistribution(z.size(0)), learn_inducing_locations=True)
        # variational_strategy = OrthogonallyDecoupledVariationalStrategy(covar_variational_strategy, z, DeltaVariationalDistribution(z.size(0)))
        super().__init__(variational_strategy)

        self.mean_module = mean
        self.covar_module = ScaleKernel(kernel)

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gp.distributions.MultivariateNormal(mean_x, covar_x)

    def predict(self, x):
        return self(x).mean.detach().numpy()

    def compute_loss(self, x, y, mll):
        output = self(x)
        # Calc loss and backprop gradients
        loss = -mll(output, y)
        loss.backward()
        return loss

    def load_cache(self, pred_dict):
        self.prediction_strategy.mean_cache.data = pred_dict["mean_cache_data"]
        self.prediction_strategy.covar_cache.data = pred_dict["covar_cache_data"]


class ExactGPModel(ExactGP):
    def __init__(self, x, y, likelihood, kernel, mean):
        super().__init__(x, y, likelihood)

        self.mean_module = mean
        self.covar_module = ScaleKernel(kernel)

    def forward(self, x):
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return gp.distributions.MultivariateNormal(mean, covar)

    def predict(self, x):
        with torch.no_grad(), gp.settings.memory_efficient(), gp.settings.fast_pred_samples(), gp.settings.fast_pred_var():
            observed_pred = self(x)
            lower, upper = observed_pred.confidence_region()
            return observed_pred.mean.numpy(), lower.numpy(), upper.numpy()

    def compute_loss(self, x, y, mll):
        output = self(x)
        # Calc loss and backprop gradients
        loss = -mll(output, y)        
        # loss.backward()
        return loss

    def load_cache(self, pred_dict, x):
        self.likelihood.noise = 1e-3
        with torch.no_grad(), gp.settings.memory_efficient(), gp.settings.fast_pred_samples(), gp.settings.fast_pred_var(), gp.settings.max_cg_iterations(100):
            self(x[0:1, :])
            self.prediction_strategy.mean_cache.data = pred_dict["mean_cache_data"]
            self.prediction_strategy.covar_cache.data = pred_dict["covar_cache_data"]


class SGPRModel(ExactGP):
    def __init__(self, x, y, num_z, likelihood, kernel, mean, initialize=True):
        super().__init__(x, y, likelihood)
        if initialize:
            k_means = MiniBatchKMeans(num_z)
            k_means = k_means.fit(x)
            z = torch.from_numpy(k_means.cluster_centers_)
        else:
            z = torch.zeros(num_z, 17)
        self.mean_module = mean
        self.base_covar_module = gp.kernels.ScaleKernel(kernel)
        self.covar_module = InducingPointKernel(self.base_covar_module, inducing_points=z, 
                                                likelihood=likelihood)

    def forward(self, x):
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return gp.distributions.MultivariateNormal(mean, covar)

    def predict(self, x):
        with torch.no_grad(), gp.settings.memory_efficient(), gp.settings.fast_pred_samples(), gp.settings.fast_pred_var():
            return self(x).mean.detach().numpy()

    def compute_loss(self, x, y, mll):
        output = self(x)
        # Calc loss and backprop gradients
        loss = -mll(output, y)        
        loss.backward()
        return loss

    def load_cache(self, pred_dict, x):
        self.likelihood.noise = 1e-3
        self(x[0:1, :])
        self.prediction_strategy.mean_cache.data = pred_dict["mean_cache_data"]
        self.prediction_strategy.covar_cache.data = pred_dict["covar_cache_data"]


class SKIPModel(ExactGP):

    def __init__(self, x, y, numZ, likelihood, kernel, mean):
        super().__init__(x, y, likelihood)
        self.mean_module = mean
        # grid_size = int(gp.utils.grid.choose_grid_size(x, kronecker_structure=False)) # if gp.utils.grid.choose_grid_size(x) > 17 else 17
        self.base_covar_module = kernel
        self.covar_module = ProductStructureKernel(
            ScaleKernel(
                GridInterpolationKernel(self.base_covar_module, grid_size=numZ, num_dims=1)
            ), num_dims=17
        )

    def forward(self, x):
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return gp.distributions.MultivariateNormal(mean, covar)

    def predict(self, x):
        with torch.no_grad(), gp.settings.memory_efficient():
            with gp.settings.fast_pred_var(), gp.settings.max_root_decomposition_size(30):
                return self(x).mean.detach().numpy()

    def compute_loss(self, x, y, mll):
        with gp.settings.max_root_decomposition_size(50), gp.settings.memory_efficient():
            output = self(x)
            # Calc loss and backprop gradients
            loss = -mll(output, y)                    
            loss.backward()
            return loss

    def load_cache(self, pred_dict, x):
        self.likelihood.noise = 1e-3
        self(x[0:1, :])
        self.prediction_strategy.mean_cache.data = pred_dict["mean_cache_data"]
        self.prediction_strategy.covar_cache.data = pred_dict["covar_cache_data"]
