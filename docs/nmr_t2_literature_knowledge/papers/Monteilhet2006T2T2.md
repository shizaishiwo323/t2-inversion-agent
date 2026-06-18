---
citation_key: Monteilhet2006T2T2
pdf: "04_pore_coupling_t2t2_interpretation\Monteilheit2006_T2-T2.pdf"
category: 04_pore_coupling_t2t2_interpretation
tags: [diffusive_coupling, exchange, ill_posed, inverse_laplace, multidimensional_nmr, nnls, peak_merging, pore_coupling, pore_coupling_t2t2_interpretation, regularization, regularized_inversion, t1_t2, t2_t2]
pages: 10
text_cache: "_extracted_text\Monteilheit2006_6a213aa5c0b8471c.txt"
---

# Monteilhet2006T2T2

- **题名/文件**：Monteilheit2006_T2-T2 (`Monteilheit2006_T2-T2.pdf`)
- **建议引用格式**：`[@Monteilhet2006T2T2]`
- **原始来源**：`NMR measurement and modeling\T2-T2\Monteilheit2006_T2-T2.pdf`
- **入选理由**：T2-T2 方法与谱解释背景。
- **在 T2 Agent 中的定位**：孔耦合/多维 NMR 解释引用；适合解释峰合并、交换和一维 T2 解释不唯一。

## Agent 可用结论

### T2-T2/T1-T2 多维 NMR 与交换
- **什么结果时调用**：当一维 T2 谱无法区分耦合/交换、流体组分或复杂孔隙环境，需要说明二维 NMR 能提供更强约束时。
- **物理/数学机制**：二维相关实验把不同等待/混合期中的弛豫相关性编码进二维谱，可揭示交换、耦合和不同流体/孔隙环境之间的关联。
- **可写入报告的引用句式**：复杂样品的一维 T2 峰不总能唯一分配给物理孔群，多维 NMR 可作为验证和补充约束。 [@Monteilhet2006T2T2]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Monteilhet2006T2T2]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 反演病态性与正则化
- **什么结果时调用**：当 T2 反演谱出现噪声振荡、假峰、正则化因子改变导致峰数/峰宽明显变化，或需要解释 NNLS/平滑约束为什么必要时。
- **物理/数学机制**：CPMG 衰减到 T2 分布是多指数/逆 Laplace 类反问题，噪声和采样范围会被放大；非负约束与平滑正则化是在拟合残差和谱平滑之间做折中。
- **可写入报告的引用句式**：T2 谱不是衰减曲线的唯一直接读数，而是受噪声、采样窗口和正则化约束影响的反演结果。 [@Monteilhet2006T2T2]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`diffusive_coupling`, `exchange`, `ill_posed`, `inverse_laplace`, `multidimensional_nmr`, `nnls`, `peak_merging`, `pore_coupling`, `pore_coupling_t2t2_interpretation`, `regularization`, `regularized_inversion`, `t1_t2`, `t2_t2`

## 证据锚点（非原文长引）

- 摘要可抽取：否；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：T2-T2/T1-T2 多维 NMR 与交换；扩散耦合与孔间交换；反演病态性与正则化。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。