---
citation_key: Tan2012T2T1Simulation
pdf: "03_numerical_methods_fem_lbm_matrix\Tan et al. - 2012 - Numerical simulation of (T2, T1) 2D NMR and fluid .pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [cpmg, echo_spacing, echo_train, exchange, forward_simulation, monte_carlo, multidimensional_nmr, numerical_methods_fem_lbm_matrix, pore_scale, pulse_sequence, random_walk, sampling, t1_t2, t2_t2]
pages: 13
text_cache: "_extracted_text\Tan2012_3a6758e66926563f.txt"
---

# Tan2012T2T1Simulation

- **题名/文件**：Tan et al. - 2012 - Numerical simulation of (T2, T1) 2D NMR and fluid .pdf (`Tan et al. - 2012 - Numerical simulation of (T2, T1) 2D NMR and fluid .pdf`)
- **建议引用格式**：`[@Tan2012T2T1Simulation]`
- **原始来源**：`NMR simulation\Echo train simulation\Tan et al. - 2012 - Numerical simulation of (T2, T1) 2D NMR and fluid .pdf`
- **入选理由**：二维 NMR/流体识别数值模拟，适合扩展到多维响应解释。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。
- **抽取备注**：PDF 可读，但有解析警告；若用于正式论文写作，请核对原文页码。

## Agent 可用结论

### T2-T2/T1-T2 多维 NMR 与交换
- **什么结果时调用**：当一维 T2 谱无法区分耦合/交换、流体组分或复杂孔隙环境，需要说明二维 NMR 能提供更强约束时。
- **物理/数学机制**：二维相关实验把不同等待/混合期中的弛豫相关性编码进二维谱，可揭示交换、耦合和不同流体/孔隙环境之间的关联。
- **可写入报告的引用句式**：复杂样品的一维 T2 峰不总能唯一分配给物理孔群，多维 NMR 可作为验证和补充约束。 [@Tan2012T2T1Simulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### CPMG/echo train 采样效应
- **什么结果时调用**：当需要解释原始衰减采样、echo spacing、早期点缺失、trim-from-peak 或模拟 echo train 对反演结果的影响时。
- **物理/数学机制**：CPMG echo train 是反演输入；采样间隔、早期信号质量、脉冲误差和噪声会影响可恢复的 T2 范围与谱稳定性。
- **可写入报告的引用句式**：T2 反演质量首先受 echo train 数据质量和时间采样窗口限制。 [@Tan2012T2T1Simulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 随机游走/Monte Carlo 正演模拟
- **什么结果时调用**：当需要解释随机游走为何能模拟 NMR 衰减、验证反演结果、或比较孔隙结构与反演 T2 谱时。
- **物理/数学机制**：随机游走把分子扩散离散为大量粒子轨迹，并在边界表面弛豫、体相弛豫和场不均匀条件下累积相位/衰减，生成可反演的 echo decay。
- **可写入报告的引用句式**：随机游走正演提供了从孔隙几何和物理参数到衰减曲线/T2 谱的机制桥梁。 [@Tan2012T2T1Simulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`cpmg`, `echo_spacing`, `echo_train`, `exchange`, `forward_simulation`, `monte_carlo`, `multidimensional_nmr`, `numerical_methods_fem_lbm_matrix`, `pore_scale`, `pulse_sequence`, `random_walk`, `sampling`, `t1_t2`, `t2_t2`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：T2-T2/T1-T2 多维 NMR 与交换；CPMG/echo train 采样效应；随机游走/Monte Carlo 正演模拟。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。