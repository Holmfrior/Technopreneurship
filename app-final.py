import streamlit as st
import requests
from streamlit_agraph import agraph, Node, Edge, Config

# Page Config
st.set_page_config(page_title="Analyzer", layout="wide")

st.title("TEXT SCANNER")
st.caption("Using Deep Learning to measure student comprehension.")

# Sidebar for Setup
with st.sidebar:
    st.header("Server Connection")
    api_url = st.text_input("Paste ngrok URL here:", value="") 
    st.info("Ensure Google Colab is running.")

# --- FUNCTION 1: CALCULATE SCORE (Depth) ---
def get_tree_depth(node):
    """
    Recursively finds the deepest level of the logic tree.
    Leaf = 1 level. Branch = 1 + deepest child.
    """
    if node.get("type") == "leaf":
        return 1
    
    children = node.get("children", [])
    if not children:
        return 1
        
    max_child_depth = 0
    for child in children:
        depth = get_tree_depth(child)
        if depth > max_child_depth:
            max_child_depth = depth
            
    return 1 + max_child_depth

# --- FUNCTION 2: PREPARE VISUALIZATION (Bubbles) ---
def get_agraph_data(node, nodes_list, edges_list, prefix, parent_id=None, my_id_suffix="0"):
    
    # Generate a Unique ID using the prefix (e.g., ref_0 or comp_0)
    my_unique_id = f"{prefix}_{my_id_suffix}"
    
    # 1. Create the Node
    relation = node.get("relation", "span").upper()
    node_type = node.get("type", "span")
    
    if node_type == "leaf":
        color = "#00C853" # Green
        full_text = node.get("text", "")
        label = full_text[:15] + "..." if len(full_text) > 15 else full_text
        size = 25
    else:
        color = "#2962FF" # Blue
        label = relation
        size = 15
        
    nodes_list.append(Node(id=my_unique_id, label=label, size=size, color=color, 
                           title=node.get("text", relation))) 

    # 2. Create Edge (Line to Parent)
    if parent_id:
        edges_list.append(Edge(source=parent_id, target=my_unique_id, color="#B0BEC5"))

    # 3. Recursion
    children = node.get("children", [])
    for index, child in enumerate(children):
        # Create a suffix like 0_1, 0_2 for children
        child_suffix = f"{my_id_suffix}_{index}"
        get_agraph_data(child, nodes_list, edges_list, prefix=prefix, parent_id=my_unique_id, my_id_suffix=child_suffix)

# --- MAIN INTERFACE ---
# --- MAIN INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("REFERENCE TEXT")
    ref_text = st.text_area("Reference Input", height=150, value="The motor stopped spinning because the fuse blew. Although the power supply was still active, no current could flow to the windings. Therefore, the circuit needs to be replaced.")

with col2:
    st.subheader("COMPARED TEXT")
    comp_text = st.text_area("Compared Input", height=150, value="The motor stopped spinning because the fuse blew. The circuit needs to be replaced.")

# --- ANALYSIS BUTTON ---
if st.button("Analyze Logic Structure", type="primary"):
    if not api_url:
        st.error("Please paste the ngrok URL from Google Colab!")
    else:
        with st.spinner("Connecting to Cloud GPU..."):
            try:
                headers = {"ngrok-skip-browser-warning": "true"}
                
                # 1. API Calls
                resp_ref = requests.post(f"{api_url}/parse", json={"text": ref_text}, headers=headers)
                resp_comp = requests.post(f"{api_url}/parse", json={"text": comp_text}, headers=headers)
                
                if resp_ref.status_code == 200 and resp_comp.status_code == 200:
                    data_ref = resp_ref.json()
                    data_comp = resp_comp.json()
                    
                    st.success("Analysis Complete!")
                    
                    # 2. CALCULATE SCORES
                    depth_ref = get_tree_depth(data_ref)
                    depth_comp = get_tree_depth(data_comp)
                    
                    if depth_ref > 0:
                        match_score = min(100, int((depth_comp / depth_ref) * 100))
                    else:
                        match_score = 0
                    
                    # 3. DISPLAY SCORES
                    st.markdown("### 📊 Cognitive Complexity Scores")
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric(label="Reference Logic Depth", value=f"{depth_ref} Levels")
                    with m2:
                        st.metric(label="Compared Logic Depth", value=f"{depth_comp} Levels", delta=f"{depth_comp - depth_ref}")
                    with m3:
                        st.metric(label="Complexity Match", value=f"{match_score}%")
                    
                    st.divider()

                    # 4. DRAW INTERACTIVE DIAGRAMS
                    config = Config(width=400, 
                                    height=400, 
                                    directed=True, 
                                    physics=True, 
                                    hierarchical=True)

                    g_col1, g_col2 = st.columns(2)
                    
                    with g_col1:
                        st.subheader("Reference Logic Map")
                        nodes_ref, edges_ref = [], []
                        # Pass prefix "ref" so IDs become "ref_0"
                        get_agraph_data(data_ref, nodes_ref, edges_ref, prefix="ref")
                        # REMOVED key="ref_viz" to fix the error
                        agraph(nodes=nodes_ref, edges=edges_ref, config=config)

                    with g_col2:
                        st.subheader("Compared Logic Map")
                        nodes_comp, edges_comp = [], []
                        # Pass prefix "comp" so IDs become "comp_0"
                        get_agraph_data(data_comp, nodes_comp, edges_comp, prefix="comp")
                        # REMOVED key="comp_viz" to fix the error
                        agraph(nodes=nodes_comp, edges=edges_comp, config=config)

                else:
                    st.error(f"Server Error: {resp_ref.status_code}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")