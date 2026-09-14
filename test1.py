# -*- coding: utf-8 -*-
import streamlit as st

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
# 單品價格
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
    # 包款
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

COSMETIC_ITEMS = ["潔顏露","紅蔘水","富勒希","滲透精華","保濕修復霜","體香噴霧","隔離"]
BAG_ITEMS = [p for p in PRICES if p not in COSMETIC_ITEMS]

# -----------------------------
# 保養品大套組
# -----------------------------
BIG_SETS = {
    ("隔離", "潔顏露", "紅蔘水", "富勒希", "保濕修復霜"): 3560,
    ("隔離", "潔顏露", "紅蔘水", "富勒希"): 2599,
    ("潔顏露", "紅蔘水", "滲透精華", "保濕修復霜"): 2880,
}

# -----------------------------
# 保養品固定組合優惠 (原價, 活動價)
# -----------------------------
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
# 折扣率排序
COMBOS_SORTED = sorted(
    COMBOS.items(),
    key=lambda x: (x[1][0]-x[1][1])/x[1][0],
    reverse=True
)

# -----------------------------
# 包款折扣規則
# -----------------------------
PACKAGE_TWO_ITEM_DISCOUNTS = [
    (["小方包"], ["短夾","零錢夾"], 0.9),
    (["長夾","掀蓋零錢夾","中夾","短夾","零錢夾"], ["法棍包"], 0.95),
    (["束口後背包", "經典後背包"], None, 0.95),  # 任二
    (["束口後背包"], ["潔顏露"], 0.9),
    (["經典後背包"], ["潔顏露"], 1680 / (1280 + 480)), # 將固定優惠價轉為乘數折扣率
    (["中夾","短夾","零錢夾"], None, 0.95),  # 任二
    (["中夾","短夾","零錢夾"], ["潔顏露","體香噴霧","隔離"], 0.9),
    (["長夾","掀蓋零錢夾"], None, 0.95),      # 任二
    (["長夾","掀蓋零錢夾"], ["潔顏露","體香噴霧","隔離"], 0.95),      
    (["巧克包"], None, 0.95),      # 任二
    (["泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"], None, 0.95), # 任二
    (["泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"] , ["潔顏露"], 0.9), 
    (["中夾","短夾","零錢夾"], ["巧克包","泡芙包(小)","泡芙包(小藍)","泡芙包(大)","泡芙包(大藍)"], 0.95)
]

# -----------------------------
# 核心計算
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
            if total<best_price:
                best_price=total
                best_plan=[(f"{'+'.join(s)} 大套組",price)]+plan
                
    # 保養品固定組合
    for c,(_,disc) in COMBOS_SORTED:
        temp = cart.copy()
        if all(temp.get(i,0)>0 for i in c):
            for i in c: temp[i]-=1
            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k,v in temp.items()))
            total = disc + new_price
            if total<best_price:
                best_price=total
                best_plan=[(f"{'+'.join(c)} 組合",disc)]+plan

    # =========================
    # 任三件9折
    # =========================
    discount_groups_3 = []

    # 1. 保養品
    cosmetics = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS:
            cosmetics += [p] * q
    discount_groups_3.append(cosmetics)

    # 2. 法棍包 + 保養品
    baguette = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p == "法棍包":
            baguette += [p] * q
    discount_groups_3.append(baguette)

    # 3. 泡芙肩背包 + 保養品
    puff = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p == "泡芙肩背包":
            puff += [p] * q
    discount_groups_3.append(puff)
    
    # 4. 零錢夾、短夾、中夾 + 保養品 (新增)
    wallets = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p in ["零錢夾", "短夾", "中夾"]:
            wallets += [p] * q
    discount_groups_3.append(wallets)

    for items in discount_groups_3:
        if len(items) >= 3:
            for group in combinations(items, 3):
                # 禁止同時出現兩種包包 (於各自陣列中已物理隔離，保留此檢查防呆)
                if "法棍包" in group and "泡芙肩背包" in group:
                    continue

                temp = cart.copy()
                valid = True
                for g in group:
                    if temp[g] <= 0:
                        valid = False
                        break
                    temp[g] -= 1

                if not valid:
                    continue

                price = int(round(sum(PRICES[g] for g in group) * 0.9))
                new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                total = price + new_price

                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任三件9折", price)] + plan

    # =========================
    # 任兩件95折
    # =========================
    discount_groups_2 = []

    # 1. 保養品
    cosmetics = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS:
            cosmetics += [p] * q
    discount_groups_2.append(cosmetics)

    # 2. 法棍包 + 保養品
    baguette = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p == "法棍包":
            baguette += [p] * q
    discount_groups_2.append(baguette)

    # 3. 泡芙肩背包 + 保養品
    puff = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p == "泡芙肩背包":
            puff += [p] * q
    discount_groups_2.append(puff)
    
    # 4. 零錢夾、短夾、中夾 + 保養品 (新增)
    wallets = []
    for p, q in cart.items():
        if p in COSMETIC_ITEMS or p in ["零錢夾", "短夾", "中夾"]:
            wallets += [p] * q
    discount_groups_2.append(wallets)

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

                if not valid:
                    continue

                price = int(round(sum(PRICES[g] for g in group) * 0.95))
                new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
                total = price + new_price

                if total < best_price:
                    best_price = total
                    best_plan = [(f"{'+'.join(group)} 任兩件95折", price)] + plan

    # 包款折扣
    for must_items, optional_items, rate in PACKAGE_TWO_ITEM_DISCOUNTS:
        if optional_items is None:
            # 任二折扣
            eligible=[]
            for item in must_items: eligible+=[item]*cart.get(item,0)
            if len(eligible)>=2:
                for group in combinations(eligible,2):
                    temp=cart.copy()
                    for g in group: temp[g]-=1
                    price=int(round(sum(PRICES[g] for g in group)*rate))
                    new_price, plan = apply_combos(tuple(f"{k}:{v}" for k,v in temp.items()))
                    total = price + new_price
                    if total<best_price:
                        best_price=total
                        best_plan=[(f"{'+'.join(group)} 任兩件{int(rate*100)}折(包包)",price)]+plan
        else:
            # 任一+任一折扣
            must_eligible=[]
            for item in must_items: must_eligible+=[item]*cart.get(item,0)
            optional_eligible=[]
            for item in optional_items: optional_eligible+=[item]*cart.get(item,0)
            if must_eligible and optional_eligible:
                for g1 in must_eligible:
                    for g2 in optional_eligible:
                        if g1!=g2 or (g1==g2 and must_eligible.count(g1)>1):
                            temp=cart.copy()
                            temp[g1]-=1
                            temp[g2]-=1
                            price=int(round((PRICES[g1]+PRICES[g2])*rate))
                            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k,v in temp.items()))
                            total=price+new_price
                            if total<best_price:
                                best_price=total
                                best_plan=[(f"{g1}+{g2} {int(rate*100)}折(包包)",price)]+plan
                                
    return best_price, best_plan

# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.set_page_config(page_title="保養品+包包組合優惠計算器", page_icon="💄", layout="wide")
    st.title("💄 組合優惠計算器")
    
    # 初始化
    for p in PRICES: st.session_state.setdefault(f"qty_{p}",0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧴 保養品")
        for p in COSMETIC_ITEMS:
            st.number_input(f"{p}", min_value=0, step=1, key=f"qty_{p}")
            st.caption(f"單價：NT${PRICES[p]:,}")
            
    with col2:
        st.subheader("👜 包款")
        for p in BAG_ITEMS:
            st.number_input(f"{p}", min_value=0, step=1, key=f"qty_{p}")
            st.caption(f"單價：NT${PRICES[p]:,}")
            
    st.markdown("---")
    st.header("🛒 商品選擇操作")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 數量全部歸零"):
            for p in PRICES: 
                st.session_state[f"qty_{p}"]=0
            st.rerun()
            
    with col_btn2:
        calc_btn = st.button("💰 計算最優價格")
            
    if calc_btn:
        cart = {p: st.session_state[f"qty_{p}"] for p in PRICES}
        if sum(cart.values())==0:
            st.warning("請先選擇商品數量喔！")
        else:
            original = calc_original(cart)
            best, plan = apply_combos(tuple(f"{k}:{v}" for k,v in cart.items()))
            st.markdown("---")
            st.subheader("💸 計算結果")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("原價總計", f"NT${original:,}")
            col_res2.metric("最優價格", f"NT${best:,}", delta=f"省下 NT${original-best:,}")
            
            st.subheader("🎯 最佳組合拆解")
            for name, price in plan:
                if "原價購買" in name and price == 0:
                    continue # 略過金額為0的原價購買顯示以保持畫面乾淨
                st.write(f"• **{name}**：NT${price:,}")
                
    with st.expander("📝 優惠規則說明", expanded=False):
        st.markdown("""
        ### 保養品與混合優惠：
        - 🎁 **大套組優惠**：依固定大套組計價  
        - 💝 **固定組合優惠**：特定保養品雙件或四件組合價  
        - 🛍️ **任兩件95折**：適用於【純保養品】或【保養品搭配 法棍包 / 泡芙肩背包 / 零錢夾 / 短夾 / 中夾】  
        - 🛍️ **任三件9折**：適用於【純保養品】或【保養品搭配 法棍包 / 泡芙肩背包 / 零錢夾 / 短夾 / 中夾】
        
        ### 包款專屬優惠：
        - 👜 **指定包款折扣**：依各檔期指定的任兩件95折、特定包款搭配9折等規則計算
        """)

if __name__=="__main__":
    main()
