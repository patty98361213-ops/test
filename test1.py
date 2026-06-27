# -*- coding: utf-8 -*-
import streamlit as st

# 🚨 強制隱藏側邊欄，讓畫面 100% 滿版
st.set_page_config(
    page_title="murfeeli 新店開幕優惠計算器", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# -----------------------------
# 🎨 注入法式奶油色系 CSS 外觀
# -----------------------------
st.markdown("""
<style>
    /* 全局背景與主體字體 */
    .stApp {
        background-color: #FDFBF7 !important;
        color: #4A3E3D !important;
    }
    
    /* 標題與副標題色調 */
    h1 {
        color: #8C7662 !important;
        font-weight: 700 !important;
    }
    h2, h3, h4, h5, h6 {
        color: #A08875 !important;
    }
    
    /* 頂部 Tabs 標籤頁樣式 */
    button[data-baseweb="tab"] {
        color: #A08875 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #6E5A4B !important;
        border-bottom-color: #C6B49F !important;
    }
    
    /* 數值輸入框樣式 */
    .stNumberInput input {
        background-color: #FFFDF9 !important;
        color: #4A3E3D !important;
        border-color: #E6DDD3 !important;
    }
    
    /* 按鈕樣式 (快速清空) */
    div.stButton > button {
        background-color: #F4EFE6 !important;
        color: #7A6555 !important;
        border: 1px solid #DCD1C4 !important;
        border-radius: 20px !important;
    }
    div.stButton > button:hover {
        background-color: #E6DDD3 !important;
        color: #5A4A3D !important;
        border-color: #C6B49F !important;
    }
    
    /* 區塊容器 (Border Container) 奶油化 */
    div[data-testid="stMetric"] {
        background-color: #F7F2E8 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid #E6DDD3 !important;
    }
    
    /* 提示框 (Alerts) 柔和化 */
    .stAlert {
        background-color: #F5EFE4 !important;
        color: #6E5A4B !important;
        border-left-color: #C6B49F !important;
    }
    
    /* 明細小字卡 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFDF9 !important;
        border: 1px solid #EAE3D5 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

from itertools import combinations
from functools import lru_cache
from collections import Counter

# -----------------------------
# 商品資料庫
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
    ("前導水", "潔顏露"): (1060, 920),
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
# 核心計算邏輯 (加入 used_cross_discount 狀態)
# -----------------------------
def calc_original(cart):
    return sum(PRICES[p] * qty for p, qty in cart.items())

@lru_cache(maxsize=None)
def apply_combos(cart_tuple, used_cross_discount=False):
    cart = {}
    for item in cart_tuple:
        parts = item.split(":")
        k = parts[0]
        v = int(parts[1])
        if v > 0:
            cart[k] = v
            
    best_price = 0
    for p, q in cart.items():
        best_price += PRICES[p] * q
        
    best_plan = []
    if best_price > 0:
        best_plan = [(f"{p} × {q} (原價)", PRICES[p] * q) for p, q in cart.items() if q > 0]
        
    # 小幫手函數：將字典轉換為排序後的 Tuple，供快取使用
    def make_tuple(t_cart):
        return tuple(sorted(f"{tk}:{tv}" for tk, tv in t_cart.items() if tv > 0))
    
    # 1. 檢查大套組優惠
    for s, price in BIG_SETS.items():
        set_counts = Counter(s)
        if all(cart.get(k, 0) >= v for k, v in set_counts.items()):
            temp = cart.copy()
            for i in s: 
                temp[i] -= 1
            new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
            total = price + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(s)} 大套組", price)] + plan
                
    # 2. 檢查固定組合優惠
    for c, (_, disc) in COMBOS_SORTED:
        combo_counts = Counter(c)
        if all(cart.get(k, 0) >= v for k, v in combo_counts.items()):
            temp = cart.copy()
            for i in c: 
                temp[i] -= 1
            new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
            total = disc + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(c)} 組合", disc)] + plan
                
    cosmetics = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS: 
            cosmetics += [p] * q

    baguette = list(cosmetics)
    if "法棍包" in cart: baguette += ["法棍包"] * cart["法棍包"]

    puff = list(cosmetics)
    if "泡芙肩背包" in cart: puff += ["泡芙肩背包"] * cart["泡芙肩背包"]

    # 3. 任三件 9 折
    for items in [cosmetics, baguette, puff]:
        if len(items) >= 3:
            for group in set(combinations(items, 3)):
                if "法棍包" in group and "泡芙肩背包" in group: continue
                temp = cart.copy()
                valid = True
                for g in group:
                    if temp.get(g, 0) <= 0:
                        valid = False
                        break
                    temp[g] -= 1
                if not valid: continue

                price = int(round(sum(PRICES[g] for g in group) * 0.9))
                new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
                total = price + new_price
                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任三件9折", price)] + plan

    # 4. 任兩件 95 折 (原版特定商品)
    for items in [cosmetics, baguette, puff]:
        if len(items) >= 2:
            for group in set(combinations(items, 2)):
                if "法棍包" in group and "泡芙肩背包" in group: continue
                temp = cart.copy()
                valid = True
                for g in group:
                    if temp.get(g, 0) <= 0:
                        valid = False
                        break
                    temp[g] -= 1
                if not valid: continue

                price = int(round(sum(PRICES[g] for g in group) * 0.95))
                new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
                total = price + new_price
                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任兩件95折", price)] + plan

    # 5. 包款與皮夾搭配折扣
    for must_items, optional_items, rate in PACKAGE_TWO_ITEM_DISCOUNTS:
        if optional_items is None:
            eligible = []
            for item in must_items: eligible += [item] * cart.get(item, 0)
            if len(eligible) >= 2:
                for group in set(combinations(eligible, 2)):
                    temp = cart.copy()
                    for g in group: temp[g] -= 1
                    
                    price = rate if rate > 1 else int(round(sum(PRICES[g] for g in group) * rate))
                    label_desc = f"組合價${rate}" if rate > 1 else f"任兩件{int(rate*100)}折"
                        
                    new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
                    total = price + new_price
                    if total < best_price:
                        best_price = total
                        best_plan = [(f"{'+'.join(group)} {label_desc}", price)] + plan
        else:
            must_eligible = []
            for item in must_items: must_eligible += [item] * cart.get(item, 0)
            optional_eligible = []
            for item in optional_items: optional_eligible += [item] * cart.get(item, 0)
            
            if must_eligible and optional_eligible:
                processed_pairs = set()
                for g1 in must_eligible:
                    for g2 in optional_eligible:
                        if g1 == g2 and must_eligible.count(g1) <= 1: continue
                        pair = tuple(sorted([g1, g2]))
                        if pair in processed_pairs: continue
                        processed_pairs.add(pair)
                        
                        temp = cart.copy()
                        temp[g1] -= 1
                        temp[g2] -= 1
                        
                        price = rate if rate > 1 else int(round((PRICES[g1] + PRICES[g2]) * rate))
                        label_desc = f"組合價${rate}" if rate > 1 else f"{int(rate*100)}折"
                            
                        new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
                        total = price + new_price
                        if total < best_price:
                            best_price = total
                            best_plan = [(f"{g1}+{g2} {label_desc}", price)] + plan

    # 🌟 6. 【新規則】全館包款任 2 件 95 折
    bag_list = []
    for p, q in cart.items():
        if p in BAG_ITEMS:
            bag_list += [p] * q

    if len(bag_list) >= 2:
        for group in set(combinations(bag_list, 2)):
            temp = cart.copy()
            for g in group:
                temp[g] -= 1

            price = int(round(sum(PRICES[g] for g in group) * 0.95))
            new_price, plan = apply_combos(make_tuple(temp), used_cross_discount)
            total = price + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(group)} 包款2件95折", price)] + plan

    # 🌟 7. 【新規則】跨品項落單 95 折 (整筆訂單限用一次)
    if not used_cross_discount:
        has_cosmetic = any(cart.get(i, 0) > 0 for i in COSMETIC_ITEMS)
        has_bag = any(cart.get(i, 0) > 0 for i in BAG_ITEMS)
        
        # 必須同時具備保養品與包包才符合跨品項門檻
        if has_cosmetic and has_bag:
            for p, q in cart.items():
                if q > 0:
                    temp = cart.copy()
                    temp[p] -= 1
                    
                    price = int(round(PRICES[p] * 0.95))
                    # 注意：這裡將 used_cross_discount 設為 True，防止同一訂單重複使用
                    new_price, plan = apply_combos(make_tuple(temp), True)
                    total = price + new_price
                    
                    if total < best_price:
                        best_price = total
                        best_plan = [(f"{p} 跨品項95折", price)] + plan
                                
    return best_price, best_plan

# -----------------------------
# UI 介面展示
# -----------------------------
def main():
    st.markdown("<h1 style='text-align: center; color: #8C7662;'>🛍️ murfeeli 新店開幕優惠計算器</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #A08875;'>✨ 支援全新【包款任 2 件 95 折】與【跨品項落單 95 折】</p>", unsafe_allow_html=True)
    st.write("")

    for p in PRICES: 
        st.session_state.setdefault(f"qty_{p}", 0)

    # 主畫面頂部控制區
    col_space, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🔄 快速清空購物車", use_container_width=True):
            for p in PRICES: st.session_state[f"qty_{p}"] = 0
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()

    tab_cosmetic, tab_bag, tab_checkout = st.tabs(["🧴 保養品", "👜 包款 / 皮夾", "🛒 結帳購物車"])

    with tab_cosmetic:
        st.subheader("選擇保養品數量")
        cols = st.columns(3)
        for idx, p in enumerate(COSMETIC_ITEMS):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**{p}**")
                    st.markdown(f"<span style='color: #8C7662;'>單價: NT${PRICES[p]:,}</span>", unsafe_allow_html=True)
                    st.number_input("數量", min_value=0, step=1, key=f"qty_{p}", label_visibility="collapsed")

    with tab_bag:
        st.subheader("選擇包款或皮夾數量")
        cols = st.columns(3)
        for idx, p in enumerate(BAG_ITEMS):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**{p}**")
                    st.markdown(f"<span style='color: #8C7662;'>單價: NT${PRICES[p]:,}</span>", unsafe_allow_html=True)
                    st.number_input("數量", min_value=0, step=1, key=f"qty_{p}", label_visibility="collapsed")

    with tab_checkout:
        st.subheader("購物清單確認")
        cart = {p: st.session_state[f"qty_{p}"] for p in PRICES if st.session_state[f"qty_{p}"] > 0}
        
        if not cart:
            st.warning("🛒 目前購物車空空如也，請先至前面分頁挑選商品。")
        else:
            for item, qty in cart.items():
                st.markdown(f"🤎 **{item}** × {qty} 件 — `NT${PRICES[item]*qty:,}`")
            
            st.markdown("---")
            
            original = calc_original(cart)
            
            cart_list = []
            for k, v in cart.items():
                cart_list.append(f"{k}:{v}")
                
            # 初始呼叫，used_cross_discount 預設為 False
            best, plan = apply_combos(tuple(sorted(cart_list)), False)
            
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
