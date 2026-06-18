---
citation_key: Toumelin2003TemperatureDiffusiveCoupling
pdf: "02_pore_scale_simulation_random_walk\Toumelin2003_Temp&DiffusiveCoupling.pdf"
category: 02_pore_scale_simulation_random_walk
tags: [cpmg, diffusive_coupling, echo_spacing, echo_train, exchange, peak_merging, pore_coupling, pore_scale_simulation_random_walk, pore_size, pulse_sequence, sampling, short_t2, surface_relaxation, surface_relaxivity]
pages: 17
text_cache: "_extracted_text\Toumelin2003_86342ccd5b7c90d4.txt"
---

# Toumelin2003TemperatureDiffusiveCoupling

- **题名/文件**：Toumelin et al. - , C. Torres-Verdín.pdf (`Toumelin2003_Temp&DiffusiveCoupling.pdf`)
- **建议引用格式**：`[@Toumelin2003TemperatureDiffusiveCoupling]`
- **原始来源**：`NMR simulation\Random Walk\Toumelin2003_Temp&DiffusiveCoupling.pdf`
- **入选理由**：温度效应与扩散耦合对 NMR 响应影响，适合解释峰展宽/峰位偏移。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。
- **抽取备注**：PDF 可读，但有解析警告；若用于正式论文写作，请核对原文页码。

## Agent 可用结论

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Toumelin2003TemperatureDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Toumelin2003TemperatureDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### CPMG/echo train 采样效应
- **什么结果时调用**：当需要解释原始衰减采样、echo spacing、早期点缺失、trim-from-peak 或模拟 echo train 对反演结果的影响时。
- **物理/数学机制**：CPMG echo train 是反演输入；采样间隔、早期信号质量、脉冲误差和噪声会影响可恢复的 T2 范围与谱稳定性。
- **可写入报告的引用句式**：T2 反演质量首先受 echo train 数据质量和时间采样窗口限制。 [@Toumelin2003TemperatureDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`cpmg`, `diffusive_coupling`, `echo_spacing`, `echo_train`, `exchange`, `peak_merging`, `pore_coupling`, `pore_scale_simulation_random_walk`, `pore_size`, `pulse_sequence`, `sampling`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：扩散耦合与孔间交换；表面弛豫、孔径与短 T2；CPMG/echo train 采样效应。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。