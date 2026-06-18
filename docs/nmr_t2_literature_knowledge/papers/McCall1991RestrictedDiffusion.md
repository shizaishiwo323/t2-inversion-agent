---
citation_key: McCall1991RestrictedDiffusion
pdf: "02_pore_scale_simulation_random_walk\McCall1991.pdf"
category: 02_pore_scale_simulation_random_walk
tags: [analytical_forward_model, eigenmodes, eigenvalues, geometry, matrix_diagonalization, pore_scale_simulation_random_walk, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 14
text_cache: "_extracted_text\Mccall1991_b846d3d70a382a51.txt"
---

# McCall1991RestrictedDiffusion

- **题名/文件**：Magnetization evolution in connected pore systems (`McCall1991.pdf`)
- **建议引用格式**：`[@McCall1991RestrictedDiffusion]`
- **原始来源**：`NMR simulation\Random Walk\McCall1991.pdf`
- **入选理由**：受限几何中的 NMR/扩散理论经典模拟参考。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。

## Agent 可用结论

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@McCall1991RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 矩阵对角化/特征模态方法
- **什么结果时调用**：当需要解释为什么复杂衰减可以表示为多个特征模态叠加，或比较随机游走/FEM 与特征值正演方法时。
- **物理/数学机制**：扩散-弛豫算子离散后可用特征值/特征向量表示，衰减曲线由多个模态贡献组成；边界条件和孔隙状态改变特征谱。
- **可写入报告的引用句式**：多指数衰减可理解为扩散-弛豫系统多个特征模态叠加，而不仅是若干孤立孔群的简单相加。 [@McCall1991RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@McCall1991RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`analytical_forward_model`, `eigenmodes`, `eigenvalues`, `geometry`, `matrix_diagonalization`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：否；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：受限扩散、几何与特征模态；矩阵对角化/特征模态方法；表面弛豫、孔径与短 T2。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。