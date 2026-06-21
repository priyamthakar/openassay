# openfit API Contract

Documented on: 2026-06-21
Source: local checkout at `D:\openassay\openfit`

## openfit version
- Declared version in `pyproject.toml`: `0.1.1`
- README status: `v0.1.2 (in progress)`

## Fit() signature
```python
Fit(
    model: str | BaseModel,
    x: array-like,
    y: array-like,
    *,
    weights: str | WeightScheme,  # REQUIRED, no silent default
    sd: array-like | None = None,
    method: str | None = None,
    p0: dict[str, float] | None = None,
    bounds: dict[str, tuple[float, float]] | None = None,
    random_seed: int = 0,
    max_nfev: int | None = None,
    xtol: float | None = None,
    ftol: float | None = None,
    gtol: float | None = None,
    x_scale: str | np.ndarray | None = None,
    diff_method: str | None = None,
)
```

## Accepted weight strings
- `"uniform"` (or `"none"`)
- `"1/y"`
- `"1/y2"`
- `"1/sd2"`
- `"poisson"`

## 4PL/5PL model IDs
- 4PL: `"hill4p"`
- 5PL: `"hill5p"`

## 4PL/5PL equations
- 4PL (`hill4p`): `y = Bottom + (Top - Bottom) / (1 + (EC50 / x)^HillSlope)`
- 5PL (`hill5p`): `y = Bottom + (Top - Bottom) / (1 + (EC50 / x)^HillSlope)^Asymmetry`

## Parameter names/order
- 4PL (`hill4p`): `["Bottom", "Top", "EC50", "HillSlope"]`
- 5PL (`hill5p`): `["Bottom", "Top", "EC50", "HillSlope", "Asymmetry"]`

## FitResult public attributes
- `params`: `dict[str, float]` - Fitted parameter values.
- `se`: `dict[str, float]` - Asymptotic standard errors.
- `ci`: `dict[str, tuple[float, float]]` - 95% confidence intervals.
- `covariance`: `np.ndarray` - Full parameter covariance matrix of shape `(n_params, n_params)`. Row/column order matches `model.param_names`. Diagonal elements equal `se[name]**2`.
- `r_squared`: `float` - Coefficient of determination.
- `aic`: `float` - Akaike Information Criterion.
- `bic`: `float` - Bayesian Information Criterion.
- `aicc`: `float` - Bias-corrected AIC.
- `rss`: `float` - Unweighted residual sum of squares.
- `x`: `np.ndarray` - Independent-variable values.
- `y`: `np.ndarray` - Observed response values.
- `y_fitted`: `np.ndarray` - Model-predicted values.
- `residuals`: `np.ndarray` - Raw residuals `y - y_fitted`.
- `weighted_residuals`: `np.ndarray` - Weighted residuals.
- `standardized_residuals`: `np.ndarray` - Residuals divided by their standard deviation.
- `n_obs`: `int` - Number of observations.
- `n_params`: `int` - Number of fitted parameters.
- `model_id`: `str` - Model identifier string.
- `weight_scheme`: `str` - Weight scheme string.
- `spec`: `FitSpec` - Full reproducibility manifest.

## Inverse prediction
- No public `inverse_predict` API is exposed in the inspected openfit checkout.
- openassay therefore performs 4PL/5PL inverse prediction from public
  `FitResult.model_id` and `FitResult.params`.
- openassay must not rely on private `FitResult._model` for back-calculation.

## Covariance availability
- **Exposed**: Yes, as of `agent/openfit-downstream-api` branch.
- **Shape**: `(n_params, n_params)`
- **Order**: Matches `model.param_names` exactly.
- **Fallback**: If Jacobian inversion fails because it is singular, filled with
  `np.nan` and standard errors are set to `inf`.
