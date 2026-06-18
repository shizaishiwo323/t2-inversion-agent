---
citation_key: EchoTrainSimulation2021
pdf: "03_numerical_methods_fem_lbm_matrix\1-s2.0-S0098300421000686-main.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [cpmg, echo_spacing, echo_train, numerical_methods_fem_lbm_matrix, pulse_sequence, sampling]
pages: 11
text_cache: "_extracted_text\EchoTrainSimulation2021_635917087f3d6ef8.txt"
---

# EchoTrainSimulation2021

- **题名/文件**：Numerical investigating the low field NMR response of representative pores at different pulse sequence parameters (`1-s2.0-S0098300421000686-main.pdf`)
- **建议引用格式**：`[@EchoTrainSimulation2021]`
- **原始来源**：`NMR simulation\Echo train simulation\1-s2.0-S0098300421000686-main.pdf`
- **入选理由**：echo train/CPMG 响应数值模拟背景，对衰减曲线生成和反演前处理有参考价值。
- **在 T2 Agent 中的定位**：采样和脉冲序列引用：CPMG echo train、pulse sequence 和数值 echo train 模拟影响；不作为 L-curve/正则化理论主引用。

## Agent 可用结论

### CPMG/echo train 采样效应
- **什么结果时调用**：当需要解释原始衰减采样、echo spacing、早期点缺失、trim-from-peak 或模拟 echo train 对反演结果的影响时。
- **物理/数学机制**：CPMG echo train 是反演输入；采样间隔、早期信号质量、脉冲误差和噪声会影响可恢复的 T2 范围与谱稳定性。
- **可写入报告的引用句式**：T2 反演质量首先受 echo train 数据质量和时间采样窗口限制。 [@EchoTrainSimulation2021]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`cpmg`, `echo_spacing`, `echo_train`, `numerical_methods_fem_lbm_matrix`, `pulse_sequence`, `sampling`

## 证据锚点（非原文长引）

- p.1 / cache line 31: 摘要关键词包含 low-field NMR response、Bloch equation、CPMG pulse sequence 和 magnetization evolution。
- p.1 / cache line 35: 文本说明基于 CPMG pulse sequence 与 Bloch equation 数值模拟 porous media 的 NMR response。
- p.1 / cache line 91: 文本指出 CPMG echo train 的 pulse imperfections 可能引入 artifacts。
- 主要证据主题：CPMG/echo train 采样效应。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。