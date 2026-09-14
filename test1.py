# -*- coding: utf-8 -*-
"""
murfeeli 優惠計算器（法式奶油風 UI + 獨立結帳頁面 + 修復 Callback Bug）
"""
import streamlit as st
from itertools import combinations
from functools import lru_cache

# -----------------------------
# 🚨 頁面配置與滿版設定
# -----------------------------
st.set_page_config(
    page_title="murfeeli優惠計算器", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# -----------------------------
# 🎨 注入法式奶油色系 CSS 外觀
# -----------------------------
# -----------------------------
# 🎨 注入法式奶油色系 CSS 外觀（已修復標籤文字顏色）
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
        letter-spacing: 1px;
    }
    h2, h3, h4, h5, h6 {
        color: #A08875 !important;
    }

    /* 🎯 修正：選項/商品標籤文字顏色（與主標題同色 #8C7662） */
    label[data-testid="stWidgetLabel"] p, 
    .stNumberInput label,
    div[data-testid="stWidgetLabel"] {
        color: #8C7662 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    /* 頂部 Tabs 標籤頁樣式 */
    button[data-baseweb="tab"] {
        color: #A08875 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #6E5A4B !important;
        border-bottom-color: #C6B49F !important;
    }
    
    /* 數值輸入框內部數字樣式 */
    .stNumberInput input {
        background-color: #FFFDF9 !important;
        color: #4A3E3D !important;
        border-color: #E6DDD3 !important;
        border-radius: 8px !important;
    }

    /* 副標題與備註小字（如單價說明） */
    .stCaption, div[data-testid="stCaptionContainer"] {
        color: #8C7662 !important;
    }
    
    /* 按鈕樣式 */
    div.stButton > button {
        background-color: #F4EFE6 !important;
        color: #7A6555 !important;
        border: 1px solid #DCD1C4 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #E6DDD3 !important;
        color: #5A4A3D !important;
        border-color: #C6B49F !important;
    }
    
    /* 數據指標卡片 */
    div[data-testid="stMetric"] {
        background-color: #F7F2E8 !important;
        padding: 16px !important;
        border-radius: 14px !important;
        border: 1px solid #E6DDD3 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    
    /* 提示框柔和化 */
    .stAlert {
        background-color: #F5EFE4 !important;
        color: #6E5A4B !important;
        border-left-color: #C6B49F !important;
        border-radius: 10px !important;
    }
    
    /* 邊框容器奶油化 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFDF9 !important;
        border: 1px solid #EAE3D5 !important;
        border-radius: 14px !important;
        padding: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 單品價格資料庫
# -----------------------------
PRICES = {
    # 保養品
    "潔顏露": 480,
    "紅蔘水": 580,
    "富勒希": 1080,
    "滲透精華": 1080,
    "保濕修復霜": 1080,
    "體香噴霧": 680,
    "隔離": 780,
    # 包款與配件
    "法棍包": 2680,
    "小方包": 2680,
    "巧克包": 2180,
    "泡芙包(小)": 1290,
    "泡芙包(小藍)": 1390,
    "泡芙包(大)": 1490,
    "泡芙包(大藍)": 1590,
    "泡芙肩背包": 1880,
    "束口後背包": 1880,
    "經典後背包": 1280,
    "中夾": 1780,
    "短夾": 1680,
    "零錢夾": 1580,
    "長夾": 2280,
    "掀蓋零錢夾": 1880,
}

COSMETIC_ITEMS = ["潔顏露", "紅蔘水", "富勒希", "滲透精華", "保濕修復霜", "體香噴霧", "隔離"]
BAG_ITEMS = [p for p in PRICES if p not in COSMETIC_ITEMS]

BIG_SETS = {
    ("隔離", "潔顏露", "紅蔘水", "富勒希", "保濕修復霜"): 3560,
    ("隔離", "潔顏露", "紅蔘水", "富勒希"): 2599,
    ("潔顏露", "紅蔘水", "滲透精華", "保濕修復霜"): 2880,
}

COMBOS = {
    ("潔顏露","潔顏露"): (960, 880),
    ("潔顏露","潔顏露","潔顏露","潔顏露"): (1920,1680),
    ("紅蔘水","紅蔘水"): (1160,1080),
    ("紅蔘水","紅蔘水","紅蔘水","紅蔘水"): (2320,2080),
    ("隔離","隔離","隔離","隔離"): (3120,2780),
    ("富勒希","富勒希"): (2160,1880),
    ("富勒希","紅蔘水"): (1660,1480),
    ("富勒希","潔顏露"): (1560,1380),
    ("紅蔘水","潔顏露"): (1060,1000),
    ("富勒希","保濕修復霜"): (2160,1980),
    ("紅蔘水","保濕修復霜"): (1660,1480),
}

COMBOS_SORTED = sorted(COMBOS.items(), key=lambda x: (x[1][0]-x[1][1])/x[1][0], reverse=True)

PACKAGE_TWO_ITEM_DISCOUNTS = [
    (["小方包"], ["短夾","零錢夾"], 0.9),
    (["長夾","掀蓋零錢夾","中夾","短夾","零錢夾"], ["法棍包"], 0.95),
    (["束口後背包", "經典後背包"], None, 0.95),
    (["束口後背包"], ["潔顏露"], 0.9),
    (["經典後背包"], ["潔顏露"], 1680 / (1280 + 480)),
    (["中夾","短夾","零錢夾"], None, 0.95),
    (["中夾","短夾","零錢夾"], ["潔顏露","體香噴霧","隔離"], 0.9),
    (["長夾","掀蓋零錢夾"], None, 0.95),
    (["長夾","掀蓋零錢夾"], ["潔顏露","體香噴霧","隔離"], 0.95),      
    (["巧克包"], None, 0.95),
    (["泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"], None, 0.95),
    (["泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"] , ["潔顏露"], 0.9), 
    (["中夾","短夾","零錢夾"], ["巧克包","泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"], 0.95)
]

# -----------------------------
# 回調函數 (清空購物車)
# -----------------------------
def reset_cart():
    for p in PRICES:
        st.session_state[f"qty_{p}"] = 0

# -----------------------------
# 核心演算法
# -----------------------------
def calc_original(cart):
    return sum(PRICES[p]*qty for p,qty in cart.items())

@lru_cache(maxsize=None)
def apply_combos(cart_tuple):
    cart = {item.split(":")[0]:int(item.split(":")[1]) for item in cart_tuple if int(item.split(":")[1])>0}
    best_price = sum(PRICES[p]*q for p,q in cart.items())
    best_plan = [("原價購買", best_price)]
    
    # 保養品大套組
    for s, price in BIG_SETS.items():
        if all(cart.get(i,0)>=1 for i in s):
            temp = cart.copy()
            for i in s: temp[i]-=1
            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k,v in temp.items()))
            total = price + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(s)} 大套組", price)] + plan
                
    # 保養品固定組合
    for c, (_, disc) in COMBOS_SORTED:
        temp = cart.copy()
        if all(temp.get(i,0)>0 for i in c):
            for i in c: temp[i]-=1
            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k,v in temp.items()))
            total = disc + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(c)} 組合", disc)] + plan

    # 任三件9折
    discount_groups_3 = []
    cosmetics = [p for p, q in cart.items() if p in COSMETIC_ITEMS for _ in range(q)]
    discount_groups_3.append(cosmetics)
    discount_groups_3.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p == "法棍包" for _ in range(q)])
    discount_groups_3.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p == "泡芙肩背包" for _ in range(q)])
    discount_groups_3.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p in ["零錢夾", "短夾", "中夾"] for _ in range(q)])

    for items in discount_groups_3:
        if len(items) >= 3:
            for group in combinations(items, 3):
                if "法棍包" in group and "泡芙肩背包" in group:
                    continue
                temp = cart.copy()
                valid = True
                for g in group:
                    if temp[g] <= 0:
                        valid = False
                        break
                    temp[g] -= 1
                if not valid: continue
                price = int(round(sum(PRICES[g] for g in group) * 0.9))
                new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                total = price + new_price
                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任三件9折", price)] + plan

    # 任兩件95折
    discount_groups_2 = []
    discount_groups_2.append(cosmetics)
    discount_groups_2.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p == "法棍包" for _ in range(q)])
    discount_groups_2.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p == "泡芙肩背包" for _ in range(q)])
    discount_groups_2.append([p for p, q in cart.items() if p in COSMETIC_ITEMS or p in ["零錢夾", "短夾", "中夾"] for _ in range(q)])

    for items in discount_groups_2:
        if len(items) >= 2:
            for group in combinations(items, 2):
                if "法棍包" in group and "泡芙肩背包" in group:
                    continue
                temp = cart.copy()
                valid = True
                for g in group:
                    if temp[g] <= 0:
                        valid = False
                        break
                    temp[g] -= 1
                if not valid: continue
                price = int(round(sum(PRICES[g] for g in group) * 0.95))
                new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                total = price + new_price
                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任兩件95折", price)] + plan

    # 包款折扣
    for must_items, optional_items, rate in PACKAGE_TWO_ITEM_DISCOUNTS:
        if optional_items is None:
            eligible = [item for item in must_items for _ in range(cart.get(item, 0))]
            if len(eligible) >= 2:
                for group in combinations(eligible, 2):
                    temp = cart.copy()
                    for g in group: temp[g] -= 1
                    price = int(round(sum(PRICES[g] for g in group) * rate))
                    new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                    total = price + new_price
                    if total < best_price:
                        best_price = total
                        best_plan = [(f"{'+'.join(group)} 任兩件{int(rate*100)}折", price)] + plan
        else:
            must_eligible = [item for item in must_items for _ in range(cart.get(item, 0))]
            optional_eligible = [item for item in optional_items for _ in range(cart.get(item, 0))]
            if must_eligible and optional_eligible:
                for g1 in must_eligible:
                    for g2 in optional_eligible:
                        if g1 != g2 or (g1 == g2 and must_eligible.count(g1) > 1):
                            temp = cart.copy()
                            temp[g1] -= 1
                            temp[g2] -= 1
                            price = int(round((PRICES[g1] + PRICES[g2]) * rate))
                            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                            total = price + new_price
                            if total < best_price:
                                best_price = total
                                best_plan = [(f"{g1}+{g2} {int(rate*100)}折", price)] + plan
                                
    return best_price, best_plan

# -----------------------------
# 🖥️ 主介面設計
# -----------------------------
def main():
    st.title("🛍️ murfeeli 優惠計算器")
    st.caption("選取商品數量後，點擊頂部「🛒 購物車結帳」頁籤即可即時試算最佳優惠")
    
    # 初始化 Session State
    for p in PRICES: 
        st.session_state.setdefault(f"qty_{p}", 0)
    
    # 三個頁籤配置
    tab1, tab2, tab3 = st.tabs(["🧴 保養系列", "👜 包款與配件", "🛒 購物車結帳"])
    
    # -----------------------------
    # Tab 1: 保養系列
    # -----------------------------
    with tab1:
        with st.container(border=True):
            st.subheader("🧴 保養品選購")
            cols = st.columns(3)
            for idx, p in enumerate(COSMETIC_ITEMS):
                with cols[idx % 3]:
                    st.number_input(
                        f"{p}", 
                        min_value=0, 
                        step=1, 
                        key=f"qty_{p}",
                        help=f"單價：NT${PRICES[p]:,}"
                    )
                    st.caption(f"NT$ {PRICES[p]:,}")

    # -----------------------------
    # Tab 2: 包款與配件
    # -----------------------------
    with tab2:
        with st.container(border=True):
            st.subheader("👜 包款與配件選購")
            cols = st.columns(3)
            for idx, p in enumerate(BAG_ITEMS):
                with cols[idx % 3]:
                    st.number_input(
                        f"{p}", 
                        min_value=0, 
                        step=1, 
                        key=f"qty_{p}",
                        help=f"單價：NT${PRICES[p]:,}"
                    )
                    st.caption(f"NT$ {PRICES[p]:,}")

    # -----------------------------
    # Tab 3: 購物車結帳頁面
    # -----------------------------
    with tab3:
        cart = {p: st.session_state[f"qty_{p}"] for p in PRICES}
        selected_items = {p: q for p, q in cart.items() if q > 0}
        total_items = sum(cart.values())
        
        if total_items == 0:
            st.info("🛒 購物車目前是空的，快到「保養系列」或「包款與配件」挑選商品吧！")
        else:
            # 結帳標題與重置按鈕 (使用 on_click callback 防止報錯)
            c_head1, c_head2 = st.columns([3, 1])
            with c_head1:
                st.subheader("📋 購物車試算明細")
            with c_head2:
                st.button("🔄 清空購物車", on_click=reset_cart, use_container_width=True)

            # 已選商品清單預覽
            with st.container(border=True):
                st.markdown("##### 📦 已選商品內容")
                cart_cols = st.columns(3)
                for idx, (p, q) in enumerate(selected_items.items()):
                    with cart_cols[idx % 3]:
                        st.markdown(f"• **{p}** × {q} （`NT$ {PRICES[p]*q:,}`）")

            st.markdown("<br>", unsafe_allow_html=True)

            # 進行最佳價格演算
            original = calc_original(cart)
            best, plan = apply_combos(tuple(f"{k}:{v}" for k, v in cart.items()))

            # 三大指標卡片
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("🛒 總件數", f"{total_items} 件")
            m_col2.metric("📋 原價總計", f"NT$ {original:,}")
            m_col3.metric("🎉 優惠折抵後", f"NT$ {best:,}", delta=f"- NT$ {original-best:,}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 組合拆解明細
            with st.container(border=True):
                st.markdown("##### 🎯 最佳組合折扣拆解")
                for name, price in plan:
                    if "原價購買" in name and price == 0:
                        continue
                    st.markdown(f"- **{name}** ： `NT$ {price:,}`")

    # 頁尾說明
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 優惠活動規則摘要", expanded=False):
        st.markdown("""
        * **保養與混合優惠**：
          * 🎁 大套組優惠 / 💝 指定保養品組合價
          * 🛍️ **任二件 95 折 / 任三件 9 折**：適用保養品，或搭配【法棍包、泡芙肩背包、零錢夾、短夾、中夾】
        * **包款專屬優惠**：
          * 👜 依各檔期指定之長夾、短夾、後背包等任二件 95 折或指定優惠價。
        """)

if __name__ == "__main__":
    main()
