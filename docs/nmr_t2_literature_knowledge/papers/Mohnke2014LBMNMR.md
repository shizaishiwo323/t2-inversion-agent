---
citation_key: Mohnke2014LBMNMR
pdf: "03_numerical_methods_fem_lbm_matrix\Mohnke2014.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [diffusive_coupling, eigenmodes, exchange, geometry, lattice_boltzmann, lbm, numerical_methods_fem_lbm_matrix, peak_merging, pore_coupling, pore_network, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 16
text_cache: "_extracted_text\Mohnke2014_d6676a41b73080e1.txt"
---

# Mohnke2014LBMNMR

- **题名/文件**：Joint numerical microscale simulations of multiphase flow and NMR relaxation behavior in porous media using Lattice Boltzmann methods (`Mohnke2014.pdf`)
- **建议引用格式**：`[@Mohnke2014LBMNMR]`
- **原始来源**：`NMR simulation\LBM\Mohnke2014.pdf`
- **入选理由**：LBM/孔尺度 NMR 模拟背景，适合和随机游走/FEM 对比。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。

## Agent 可用结论

### LBM 扩散/弛豫模拟
- **什么结果时调用**：当需要解释 lattice Boltzmann 方法为何适合孔尺度扩散、复杂边界和连通孔隙正演时。
- **物理/数学机制**：LBM 在格点上推进分布函数，能够处理复杂边界与孔隙连通结构中的扩散过程，并可与表面弛豫边界结合。
- **可写入报告的引用句式**：LBM 是连接数字孔隙结构和 NMR 衰减响应的一种孔尺度数值方法。 [@Mohnke2014LBMNMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Mohnke2014LBMNMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Mohnke2014LBMNMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Mohnke2014LBMNMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`diffusive_coupling`, `eigenmodes`, `exchange`, `geometry`, `lattice_boltzmann`, `lbm`, `numerical_methods_fem_lbm_matrix`, `peak_merging`, `pore_coupling`, `pore_network`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：LBM 扩散/弛豫模拟；表面弛豫、孔径与短 T2；扩散耦合与孔间交换；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。