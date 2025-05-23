# 실행 환경 python 3.11.11

import subprocess
import sys

def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for lib in ["matplotlib", "gradio"]:
    install_if_missing(lib)

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import gradio as gr
import tempfile
import time
import threading
import os
import webbrowser

class LinkedBinaryTree:
    class _Node:
        __slots__ = "_element", "_parent", "_left", "_right"
        def __init__(self, element, parent=None, left=None, right=None):
            self._element = element
            self._parent = parent
            self._left = left
            self._right = right

    class Position:
        def __init__(self, container, node):
            self._container = container
            self._node = node
        def element(self):
            return self._node._element

    def _validate(self, p):
        return p._node

    def _make_position(self, node):
        return self.Position(self, node) if node else None

    def __init__(self):
        self._root = None
        self._size = 0

    def root(self):
        return self._make_position(self._root)

    def add_root(self, e):
        self._root = self._Node(e)
        self._size = 1
        return self._make_position(self._root)

    def add_left(self, p, e):
        node = self._validate(p)
        node._left = self._Node(e, parent=node)
        self._size += 1
        return self._make_position(node._left)

    def add_right(self, p, e):
        node = self._validate(p)
        node._right = self._Node(e, parent=node)
        self._size += 1
        return self._make_position(node._right)

def build_expression_tree():
    T = LinkedBinaryTree()
    root = T.add_root("+")
    left = T.add_left(root, "*")
    right = T.add_right(root, "*")
    T.add_left(left, "2")
    minus = T.add_right(left, "-")
    T.add_left(minus, "a")
    T.add_right(minus, "1")
    T.add_left(right, "3")
    T.add_right(right, "b")
    return T

def render_expression_stepwise(node, visited, output):
    if node is None:
        return
    left = node._left
    right = node._right
    is_inner = left or right
    if is_inner and left and left in visited:
        output.append("(")
    if left:
        render_expression_stepwise(left, visited, output)
    if node in visited:
        output.append(node._element)
    if right:
        render_expression_stepwise(right, visited, output)
    if is_inner and right and right in visited:
        output.append(")")

def collect_sequence(tree, mode):
    result = []
    def _preorder(p):
        result.append(p)
        node = tree._validate(p)
        if node._left:
            _preorder(tree._make_position(node._left))
        if node._right:
            _preorder(tree._make_position(node._right))

    def _inorder(p):
        node = tree._validate(p)
        if node._left:
            _inorder(tree._make_position(node._left))
        result.append(p)
        if node._right:
            _inorder(tree._make_position(node._right))

    def _postorder(p):
        node = tree._validate(p)
        if node._left:
            _postorder(tree._make_position(node._left))
        if node._right:
            _postorder(tree._make_position(node._right))
        result.append(p)

    root = tree.root()
    if mode == "Inorder":
        _inorder(root)
    elif mode == "Preorder":
        _preorder(root)
    elif mode == "Postorder":
        _postorder(root)
    return result

def layout_tree(tree):
    pos = {}
    x_counter = [0]
    def dfs(node, depth=0):
        if node._left:
            dfs(node._left, depth + 1)
        pos[node] = (x_counter[0], -depth)
        x_counter[0] += 1
        if node._right:
            dfs(node._right, depth + 1)
    root = tree._validate(tree.root())
    dfs(root)
    xs = [x for x, y in pos.values()]
    shift = (max(xs) + min(xs)) / 2
    for k in pos:
        x, y = pos[k]
        pos[k] = (x - shift, y)
    return pos

def draw_tree(tree, highlight=None, visited=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_aspect('equal')
    ax.axis("off")
    pos = layout_tree(tree)

    def get_node_color(node):
        if visited and any(tree._validate(v) is node for v in visited):
            return "lightgreen"
        if highlight and tree._validate(highlight) is node:
            return "orange"
        return "skyblue"

    for p in pos:
        x, y = pos[p]
        if p._left:
            cx, cy = pos[p._left]
            ax.plot([x, cx], [y, cy], 'k-', zorder=1)
        if p._right:
            cx, cy = pos[p._right]
            ax.plot([x, cx], [y, cy], 'k-', zorder=1)

    for p in pos:
        x, y = pos[p]
        node_color = get_node_color(p)
        circle = patches.Circle((x, y), 0.4, facecolor=node_color, edgecolor='black', zorder=2)
        ax.add_patch(circle)
        ax.text(x, y, p._element, fontsize=14, ha='center', va='center', zorder=3)

    path = os.path.join(tempfile.gettempdir(), f"tree_{time.time()}.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    return path

def run_ui(tree):
    stop_flag = threading.Event()

    def animate_and_update(mode):
        seq = collect_sequence(tree, mode)
        visited = []
        for p in seq:
            if stop_flag.is_set():
                break
            visited.append(p)
            img_path = draw_tree(tree, highlight=p, visited=visited)
            if mode == "Inorder":
                visited_nodes = set(tree._validate(v) for v in visited)
                output = []
                render_expression_stepwise(tree._validate(tree.root()), visited_nodes, output)
                expr_html = ''.join(output)
            else:
                expr_html = ''.join(n.element() for n in visited)
            html_expr = f"""
            <div style='text-align:center; font-size:28px; font-weight:bold;'>
                {expr_html}
            </div>
            """
            yield img_path, html_expr
            time.sleep(0.6)
        stop_flag.clear()

    def show_step(step, mode):
        seq = collect_sequence(tree, mode)
        p = seq[step] if step < len(seq) else None
        img_path = draw_tree(tree, highlight=p, visited=seq[:step])
        if mode == "Inorder":
            visited_nodes = set(tree._validate(v) for v in seq[:step+1])
            output = []
            render_expression_stepwise(tree._validate(tree.root()), visited_nodes, output)
            expr_html = ''.join(output)
        else:
            expr_html = ''.join(n.element() for n in seq[:step+1])
        html_expr = f"""
        <div style='text-align:center; font-size:28px; font-weight:bold;'>
            {expr_html}
        </div>
        """
        return img_path, html_expr

    with gr.Blocks() as demo:
        gr.Markdown("# Arithmetic Expression Tree Traversal Animation")
        with gr.Row():
            mode = gr.Radio(["Inorder", "Preorder", "Postorder"], value="Inorder", label="Traversal Mode")
            step = gr.Slider(minimum=0, maximum=10, step=1, value=0, label="Step")
        img = gr.Image(type="filepath", label="Tree")
        expr = gr.HTML("<div style='text-align:center; font-size:28px; font-weight:bold;'>수식이 여기에 표시됩니다</div>")

        step.change(show_step, [step, mode], [img, expr])
        mode.change(show_step, [step, mode], [img, expr])
        animate_btn = gr.Button("▶ 애니메이션 실행")
        stop_btn = gr.Button("⏹ 정지")
        animate_btn.click(animate_and_update, inputs=mode, outputs=[img, expr])
        stop_btn.click(fn=lambda: stop_flag.set(), inputs=None, outputs=None)

        threading.Thread(target=lambda: webbrowser.open("http://127.0.0.1:7860"), daemon=True).start()
        demo.launch()

if __name__ == "__main__":
    tree = build_expression_tree()
    run_ui(tree)
