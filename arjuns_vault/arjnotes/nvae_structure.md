TODO: This is currently incomplete

Terminology:
- $x$: input
- $E_i$: encoder block at $i$ th level
- $h_i$: output of encoder block at $i$ th level
- $d^{m,s}_i$: deviation from prior distribution at $i$ th level. $m$ stands for mu, $s$ stands for sigma. Note: actual prediction is logvar, sigma is derived from it.
- $z^{m,s}_i$: posterior distribution at $i$ th level
- $p^{m,s}_i$: prior distribution at $i$ th level
- $D_i$: decoder block at $i$ th level
- $r_i$: output of decoder block at $i$ th level
- $LE_i$: latent encoders at $i$ th level. These reduce the dimensions to desired number of channels and estimate mu and logvar.
- $LD_i$: latent decoders at $i$ th level
- $ECM$, $DCM$: encoder and decoder channel mappers

---

Assumptions:
- Prior of deepest level is standard normal. In the paper, this is actually derived from a learnable vector. They use $h$ in the paper. It is ommited in this diagram.

---

Here is how the NVAE training process for a depth of 3 looks like:

```math
\begin{aligned}

x & \xrightarrow{ECM} & h_0 & \xrightarrow{E1} & h_1 \\
&&&& \downarrow \\
&&&&& \xrightarrow{E2} & h_2 & \xrightarrow{LE_2} \xrightarrow{} &&&&&&&& p^{m,s}_2 \\
&&&&&& \downarrow &&&&&&&& \uparrow\hspace{1em} \\
&&&&&&& \xrightarrow{E3} & h_3 & \xrightarrow{LE_3} & d^{m,s}_3 & + & p^{m,s}_3 & \xrightarrow{} & z^{m,s}_3 & \xrightarrow{sample} & z_3  \\




\end{aligned}
```
