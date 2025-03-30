Some youtube links can be found in youtube.md

---

Terminology:
- $x$: Our observed data i.e. our dataset
- $z$: Latent representation of the data
- $p(z)$: Our prior i.e. our assumption of what the latent space looks like. Usually assumed to be standard normal
- $p(z|x)$: Posterior i.e. the actual distribution of the latent space given our observed data. This is approximated by our VAE encoder
- $p(x|z)$: Likelihood function i.e. the likelihood of x being true given the latent representation. This is estimated by our VAE decoder
- $p(x)$: Marginal likelihood i.e. the likelihood of x being true (what we want) over all possible z

Note that all of these are parameterized by our model i.e. subscript $\theta$

---

Goal:
To maximize $p(x)$ as that means maximizing the likelihood of our data being generated

---

Explanation of how VAEs work:

According to Bayes' theorem:

$$p(x) = \frac{p(x|z)p(z)}{p(z|x)}$$

Taking $\log$ on both sides:

$$\log p(x) = \log p(x|z) + \log p(z) - \log p(z|x)$$

Note that the true posterior $p(z|x)$ is intractable (because it itself requires the value of $p(x)$ to be known) and has to be estimated using a network i.e. the VAE encoder

This equation is mathematically sound for a specific value of $z$. However, in VAE, we need to reason about expectations across the latent variable distribution.

Taking the expectation with respect to our variational distribution $q(z|x)$ on both sides, we get:

<!-- Spaces have been added after the underscores because otherwise GitHub preview assumes I am using italics -->
$$\mathbb{E}_ {z \sim q(z|x)}[\log p(x)] = \mathbb{E}_ {z \sim q(z|x)}[\log p(x|z) + \log p(z) - \log p(z|x)]$$

$\log p(x)$ is constant with respect to $z$, also we add and subtract $\mathbb{E}_ {z \sim q(z|x)}[\log q(z|x)]$:

$$\log p(x) = \mathbb{E}_ {z \sim q(z|x)}[\log p(x|z) - \underline{\log q(z|x)} + \log p(z) + \underline{\log q(z|x)} - \log p(z|x)]$$

Now we split the terms:

$$\log p(x) = \mathbb{E}_ {z \sim q(z|x)}[\log p(x|z)] - \mathbb{E}_ {z \sim q(z|x)}[\log q(z|x) - \log p(z)] + \mathbb{E}_ {z \sim q(z|x)}[\log q(z|x) - \log p(z|x)]$$

Rearranging:

$$\log p(x) = \mathbb{E}_ {z \sim q(z|x)}[\log p(x|z)] - \mathbb{E}_ {z \sim q(z|x)}\left[\log \frac{q(z|x)}{p(z)}\right] + \mathbb{E}_ {z \sim q(z|x)}\left[\log \frac{q(z|x)}{p(z|x)}\right]$$

This can be written in terms of KL-divergence:

Rearranging, we get:

$$\log p(x) = \underbrace{\mathbb{E}_ {z \sim q(z|x)}[\log p(x|z)] - D_ {KL}[q(z|x) \| p(z)]}_ {\text{ELBO}} + \underbrace{D_ {KL}[q(z|x) \| p(z|x)]}_ {>=0}$$

Remember that $p(z|x)$ is intractable, but since KL divergence is always $>=0$, we can safely say:

$$\log p(x) >= \underbrace{\mathbb{E}_ {z \sim q(z|x)}[\log p(x|z)]}_ {\text{Minimize NLL i.e. reconstruction loss}} - \underbrace{D_ {KL}[q(z|x) \| p(z)]}_ {\text{KL Divergence between estimated posterior and assumed prior}} = \text{ELBO}$$


If we maximize the ELBO, we approximately maximize $\log p(x)$

---
