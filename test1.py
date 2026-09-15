# -*- coding: utf-8 -*-
import streamlit as st
from itertools import combinations
from functools import lru_cache
from collections import Counter

# 🚨 強制隱藏側邊欄，讓畫面 100% 滿版
st.set_page_config(
    page_title="murfeeli優惠計算器", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# -----------------------------
# 🎨 注入法式奶油色系 CSS 外觀
# -----------------------------
st.markdown("""
<style>
    .stApp { background-color: #FDFBF7 !important; color: #4A3E3D !important; }
    h1 { color: #8C7662 !important; font-weight: 700 !important; }
    h2, h3, h4, h5, h6 { color: #A08875 !important; }
    button[data-baseweb="tab"] { color: #A08875 !important; font-weight: 600 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #6E5A4B !important; border-bottom-color: #C6B49F !important; }
    .stNumberInput input { background-color: #FFFDF9 !important; color: #4A3E3D !important; border-color: #E6DDD3 !important; }
    div.stButton > button { background-color: #F4EFE6 !important; color: #7A6555 !important; border: 1px solid #DCD1C4 !important; border-radius: 20px !important; }
    div.stButton > button:hover { background-color: #E6DDD3 !important; color: #5A4A3D !important; border-color: #C6B49F !important; }
    div[data-testid="stMetric"] { background-color: #F7F2E8 !important; padding: 15px !important; border-radius: 12px !important; border: 1px solid #E6DDD3 !important; }
    .stAlert { background-color: #F5EFE4 !important; color: #6E5A4B !important; border-left-color: #C6B49F !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFDF9 !important; border: 1px solid #EAE3D5 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 商品資料庫與規則定義
# -----------------------------
PRICES = {
    "潔顏露": 480, "前導水": 580, "富勒烯": 1080, "滲透精華": 1080, 
    "保濕修復霜": 1080, "體香噴霧": 680, "隔離": 780,
    "法棍包": 2680, "小方包": 2680, "巧克包": 2180, "馬鞍包": 2280, "泡芙包(小)": 1290, 
    "泡芙包(小藍)": 1390, "泡芙包(大)": 1490, "泡芙包(大藍)": 1590, 
    "泡芙肩背包": 1880, "束口後背包": 1880, "經典後背包": 1280, 
    "中夾": 1780, "短夾": 1680, "零錢夾": 1580, "長夾": 2280, "掀蓋零錢夾": 1880
}

COSMETIC_ITEMS = ["潔顏露", "前導水", "富勒烯", "滲透精華", "保濕修復霜", "體香噴霧", "隔離"]
BAG_ITEMS = [p for p in PRICES if p not in COSMETIC_ITEMS]

# 獨立混搭群組（不可跨組混搭）
MIX_GROUPS = [
    set(COSMETIC_ITEMS + ["泡芙肩背包"]),
    set(COSMETIC_ITEMS + ["法棍包"]),
    set(COSMETIC_ITEMS + ["中夾", "短夾", "零錢夾"]),
]

BIG_SETS = {
    ("隔離", "潔顏露", "前導水", "富勒烯", "保濕修復霜"): 3560,
    ("隔離", "潔顏露", "前導水", "富勒烯"): 2599,
    ("潔顏露", "前導水", "滲透精華", "保濕修復霜"): 2880,
}

COMBOS = {
    ("潔顏露", "潔顏露"): (960, 880),
    ("潔顏露", "潔顏露", "潔顏露", "潔顏露"): (1920, 1680),
    ("前導水", "前導水"): (1160, 1080),
    ("前導水", "前導水", "前導水", "前導水"): (2320, 2080),
    ("隔離", "隔離", "隔離", "隔離"): (3120, 2780),
    ("富勒烯", "富勒烯"): (2160, 1880),
    ("富勒烯", "前導水"): (1660, 1480),
    ("富勒烯", "潔顏露"): (1560, 1380),
    ("前導水", "潔顏露"): (1060, 1000),
    ("富勒烯", "保濕修復霜"): (2160, 1980),
    ("前導水", "保濕修復霜"): (1660, 1480),
}
COMBOS_SORTED = sorted(COMBOS.items(), key=lambda x: (x[1][0] - x[1][1]) / x[1][0], reverse=True)

PACKAGE_TWO_ITEM_DISCOUNTS = [
    (["小方包"], ["短夾", "零錢夾"], 0.9),
    (["長夾", "掀蓋零錢夾", "中夾", "短夾", "零錢夾"], ["法棍包"], 0.95),
    (["束口後背包", "經典後背包"], None, 0.95),  
    (["束口後背包"], ["潔顏露"], 0.9),
    (["經典後背包"], ["潔顏露"], 1680),           
    (["中夾", "短夾", "零錢夾"], None, 0.95),       
    (["中夾", "短夾", "零錢夾"], ["潔顏露", "體香噴霧", "隔離"], 0.9),
    (["長夾", "掀蓋零錢夾"], None, 0.95),           
    (["長夾", "掀蓋零錢夾"], ["潔顏露", "體香噴霧", "隔離"], 0.95),      
    (["巧克包"], None, 0.95),                       
    (["泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], None, 0.95), 
    (["泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], ["潔顏露"], 0.9), 
    (["中夾", "短夾", "零錢夾"], ["巧克包", "泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], 0.95) 
]

# -----------------------------
# 工具函式
# -----------------------------
def cart_to_tuple(cart):
    return tuple(f"{k}:{v}" for k, v in cart.items() if v > 0)

def tuple_to_cart(cart_tuple):
    cart = {}
    for item in cart_tuple:
        k, v = item.split(":")
        if int(v) > 0: cart[k] = int(v)
    return cart

def calc_original(cart):
    return sum(PRICES[p] * qty for p, qty in cart.items())

# -----------------------------
# 核心計算邏輯
# -----------------------------
@lru_cache(maxsize=None)
def apply_combos(cart_tuple):
    cart = tuple_to_cart(cart_tuple)
    
    best_price = sum(PRICES[p] * q for p, q in cart.items())
    best_plan = [(f"{p} × {q} (原價)", PRICES[p] * q) for p, q in cart.items()] if best_price > 0 else []

    # 1. 大套組優惠
    for s, price in BIG_SETS.items():
        counts = Counter(s)
        if all(cart.get(k, 0) >= v for k, v in counts.items()):
            temp = cart.copy()
            for i in s: temp[i] -= 1
            new_price, plan = apply_combos(cart_to_tuple(temp))
            if price + new_price < best_price:
                best_price, best_plan = price + new_price, [(f"{'+'.join(s)} 大套組", price)] + plan

    # 2. 固定組合優惠
    for c, (_, disc) in COMBOS_SORTED:
        counts = Counter(c)
        if all(cart.get(k, 0) >= v for k, v in counts.items()):
            temp = cart.copy()
            for i in c: temp[i] -= 1
            new_price, plan = apply_combos(cart_to_tuple(temp))
            if disc + new_price < best_price:
                best_price, best_plan = disc + new_price, [(f"{'+'.join(c)} 組合", disc)] + plan

    # 3 & 4. 獨立群組湊件折扣 (任三件9折 / 任兩件95折)
    for discount_rate, min_qty, label in [(0.9, 3, "任三件9折"), (0.95, 2, "任兩件95折")]:
        for group_allowed in MIX_GROUPS:
            pool = [p for p in cart for _ in range(cart[p]) if p in group_allowed]
            if len(pool) >= min_qty:
                for group in set(combinations(pool, min_qty)):
                    temp = cart.copy()
                    for g in group: temp[g] -= 1
                    price = int(round(sum(PRICES[g] for g in group) * discount_rate))
                    new_price, plan = apply_combos(cart_to_tuple(temp))
                    if price + new_price < best_price:
                        best_price, best_plan = price + new_price, [(f"{'+'.join(group)} {label}", price)] + plan

    # 5. 特定兩件搭配折扣
    for must_items, optional_items, rate in PACKAGE_TWO_ITEM_DISCOUNTS:
        if optional_items is None:
            eligible = [item for item in must_items for _ in range(cart.get(item, 0))]
            if len(eligible) >= 2:
                for group in set(combinations(eligible, 2)):
                    temp = cart.copy()
                    for g in group: temp[g] -= 1
                    price = rate if rate > 1 else int(round(sum(PRICES[g] for g in group) * rate))
                    label_desc = f"組合價${rate}" if rate > 1 else f"任兩件{int(rate*100)}折"
                    new_price, plan = apply_combos(cart_to_tuple(temp))
                    if price + new_price < best_price:
                        best_price, best_plan = price + new_price, [(f"{'+'.join(group)} {label_desc}", price)] + plan
        else:
            must_eligible = [item for item in must_items for _ in range(cart.get(item, 0))]
            opt_eligible = [item for item in optional_items for _ in range(cart.get(item, 0))]
            if must_eligible and opt_eligible:
                processed_pairs = set()
                for g1 in must_eligible:
                    for g2 in opt_eligible:
                        if g1 == g2 and must_eligible.count(g1) <= 1: continue
                        pair = tuple(sorted([g1, g2]))
                        if pair in processed_pairs: continue
                        processed_pairs.add(pair)

                        temp = cart.copy()
                        temp[g1] -= 1
                        temp[g2] -= 1
                        price = rate if rate > 1 else int(round((PRICES[g1] + PRICES[g2]) * rate))
                        label_desc = f"組合價${rate}" if rate > 1 else f"{int(rate*100)}折"
                        new_price, plan = apply_combos(cart_to_tuple(temp))
                        if price + new_price < best_price:
                            best_price, best_plan = price + new_price, [(f"{g1}+{g2} {label_desc}", price)] + plan

    return best_price, best_plan

# -----------------------------
# UI 介面展示
# -----------------------------
def render_item_grid(title, item_list):
    st.subheader(title)
    cols = st.columns(3)
    for idx, p in enumerate(item_list):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{p}**")
                st.markdown(f"<span style='color: #8C7662;'>單價: NT${PRICES[p]:,}</span>", unsafe_allow_html=True)
                st.number_input("數量", min_value=0, step=1, key=f"qty_{p}", label_visibility="collapsed")

def main():
    st.markdown("<h1 style='text-align: center; color: #8C7662;'>🛍️ murfeeli優惠計算器</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #A08875;'>即時精算全店最優組合優惠價</p>", unsafe_allow_html=True)
    st.write("")

    for p in PRICES: 
        st.session_state.setdefault(f"qty_{p}", 0)

    # 頂部控制區
    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🔄 快速清空購物車", use_container_width=True):
            for p in PRICES: st.session_state[f"qty_{p}"] = 0
            st.rerun()

    tab_cosmetic, tab_bag, tab_checkout = st.tabs(["🧴 保養品", "👜 包款 / 皮夾", "🛒 結帳購物車"])

    with tab_cosmetic:
        render_item_grid("選擇保養品數量", COSMETIC_ITEMS)

    with tab_bag:
        render_item_grid("選擇包款或皮夾數量", BAG_ITEMS)

    with tab_checkout:
        cart = {p: st.session_state[f"qty_{p}"] for p in PRICES if st.session_state[f"qty_{p}"] > 0}
        total_items = sum(cart.values())
        
        st.subheader(f"購物清單確認（共 {total_items} 件）")
        
        if not cart:
            st.warning("🛒 目前購物車空空如也，請先至前面分頁挑選商品。")
        else:
            for item, qty in cart.items():
                st.markdown(f"🤎 **{item}** × {qty} 件 — `NT${PRICES[item]*qty:,}`")
            
            st.markdown("---")
            
            original = calc_original(cart)
            best, plan = apply_combos(cart_to_tuple(cart))
            
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.metric(label="商品原價合計", value=f"NT$ {original:,}")
            with res_col2:
                st.metric(label="✨ 最優折扣價", value=f"NT$ {best:,}")
            with res_col3:
                st.metric(label="💰 現省金額", value=f"NT$ {original - best:,}", delta=f"已省 ${original - best:,}")
                
            st.write("")
            
            with st.container(border=True):
                st.markdown("### 🎯 最佳優惠搭配組合方案")
                display_plan = [f"✅ {name} → `NT${price:,}`" for name, price in plan if price > 0]
                if display_plan:
                    for item in display_plan:
                        st.markdown(item)
                else:
                    st.markdown("• 本單查無適用組合。")

if __name__ == "__main__":
    main()
