# Lab 4
**重要提醒**
1. 本Lab非小组Lab，需独立完成。
2. 所有的代码都需要在原小组代码的基础上进行重构，即其它功能也需要实现。如果选择完全重新实现，会扣除个人Lab的 20% 的得分。
3. 提交文件名：`<groupId>-<学号>-<姓名>-lab4.zip`


## 树形结构显示的重构

根据review的结果，几乎所有的小组，对于两个树形结构的打印都是单独实现，尽管由于大模型的能力的增强，现在可以很方便地独立实现树形结构的输出，但这会导致相同的逻辑分散在不同的地方，增加了维护的难度。

树形结构的显示是一个常见的需求，设计模式中，适配器模式的一个典型案例就是将不同的数据显示为一个TreeView。接下来的Lab要求每位同学在自己小组代码的基础上，重构现有的代码，使用适配器模式构造一组接口/类，能够将不同的结构适配为一个TreeView。

步骤如下：

1. 查找、学习如何使用适配器模式来模块化树形结构的显示。
   - **参考链接**：
     - [InfoWorld: Adopt Adapter (Using JTree TreeModel as an example)](https://www.infoworld.com/article/2073748/adopt-adapter.html)
     - [Programming in the Large: Adapter Pattern (File System to JTree)](https://apprize.best/programming/large/5.html)
     - [Refactoring.Guru: Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
2. 学习 VS Code 中如何开发树形结构视图（Tree View）插件，重点分析其核心接口与实现机制。
   - **参考链接**：
     - [VS Code Extension Guide: Tree View](https://code.visualstudio.com/api/extension-guides/tree-view)
     - [VS Code API Reference: TreeDataProvider](https://code.visualstudio.com/api/references/vscode-api#TreeDataProvider)
     - [GitHub Sample: Tree View Example](https://github.com/microsoft/vscode-extension-samples/tree/main/tree-view-sample)
  
    注意：vscode中的treeview是一个图形界面，我们需要实现的是一个简化的版本，只需要用制表符输出到控制台上。
  
3. 设计和实现适配器模式的接口/类，能够将不同的结构适配为一个TreeView, 将当前代码中打印文件目录和打印xml结构的部分改造为使用适配器模式实现。


## 提交的内容：
1. 提交重构后的代码，包含适配器模式的接口/类。要求在原小组代码的基础上重构，即其它功能也需要实现。
2. 一个短视频（1-2分钟），先展示改造后的与树形结构相关的代码结构，然后运行代码，展示两个树形结构的显示。
3. 一个简单的文档，内容包括
    * vscode中树形结构的插件的实现以及与适配器模式的关系。
    * 重构的代码是如何使用适配器模式来实现树形结构的显示。
    * 结合Lab的开发过程，分析大模型在开发中的角色，以及应该如何更好地利用大模型进行软件开发。
4. 提交文件名：`<groupId>-<学号>-<姓名>-lab4.zip`
