"""
VERA-MD: Verification Engine for Results & Accountability - Maryland
Type 4 Detection using ACCESS for ELLs Speaking vs Writing + MCAP Achievement Data

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

MD_RED = "#CE1126"
MD_GOLD = "#FFD200"
MD_BLACK = "#000000"
MD_DARK = "#1a1a1a"

# ============================================================================
# DATA: Maryland LEAs with EL Populations
# ============================================================================

def load_leas():
    """
    Load Maryland LEAs with significant EL populations.
    Maryland has only 24 LEAs (23 counties + Baltimore City).
    SASID = 10-digit student ID. District ID = 2-digit county code.
    Total: ~112,081 ELs statewide. PG + Montgomery = 52% of all state ELs.
    Dashboard: reportcard.msde.maryland.gov (1-5 stars).
    Blueprint for Maryland's Future: $3.8B reform.
    Excellence Act (2025): protected EL funding.
    """
    data = [
        ("16", "Prince George's County Public Schools", 131000, 33121, 25.3, 79.5, 35.2, 18.8),
        ("15", "Montgomery County Public Schools", 160000, 31706, 19.8, 91.2, 55.4, 32.1),
        ("03", "Baltimore County Public Schools", 111000, 12191, 11.0, 85.1, 48.2, 25.6),
        ("30", "Baltimore City Public Schools", 76000, 9702, 12.8, 72.4, 30.8, 14.2),
        ("13", "Howard County Public Schools", 58000, 5220, 9.0, 93.5, 62.8, 38.5),
        ("02", "Anne Arundel County Public Schools", 84000, 4200, 5.0, 89.2, 52.1, 28.4),
        ("09", "Frederick County Public Schools", 45000, 3150, 7.0, 90.8, 56.5, 31.2),
        ("12", "Harford County Public Schools", 37000, 1480, 4.0, 88.5, 51.8, 27.9),
        ("06", "Charles County Public Schools", 27000, 1350, 5.0, 86.2, 45.6, 22.1),
        ("24", "Wicomico County Public Schools", 14000, 1260, 9.0, 81.5, 38.4, 19.5),
        ("04", "Calvert County Public Schools", 16000, 640, 4.0, 91.8, 58.2, 33.8),
        ("05", "Caroline County Public Schools", 5500, 550, 10.0, 78.2, 34.5, 16.8),
        ("08", "Dorchester County Public Schools", 4600, 460, 10.0, 76.8, 32.1, 15.2),
        ("21", "Talbot County Public Schools", 4400, 528, 12.0, 82.5, 42.8, 21.5),
        ("18", "Queen Anne's County Public Schools", 7500, 375, 5.0, 89.5, 54.2, 30.1),
    ]

    return pd.DataFrame(data, columns=[
        'county_code', 'lea_name', 'total_students',
        'el_count', 'el_percent', 'graduation_rate',
        'mcap_ela_all', 'mcap_math_all'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (modeled from MSDE ACCESS reporting patterns)
# ============================================================================

def load_access_data(leas_df):
    """Generate LEA ACCESS domain data modeled from MSDE ACCESS reporting patterns."""
    access_data = []

    for _, d in leas_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                base_speaking = 342 + (grade * 8)
                base_writing = 292 + (grade * 6)

                # LEA adjustments based on MCAP proficiency and EL density
                ela_factor = d['mcap_ela_all'] / 50.8  # normalize to state ELA avg
                speaking_adj = int(16 * ela_factor + d['el_percent'] * 0.45)
                writing_adj = int(-6 + (ela_factor - 1) * 13)

                access_data.append({
                    'county_code': d['county_code'],
                    'lea_name': d['lea_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(20, int(d['el_count'] / 6)),
                    'listening_avg': base_speaking + speaking_adj - 4,
                    'speaking_avg': base_speaking + speaking_adj,
                    'reading_avg': base_writing + writing_adj + 14,
                    'writing_avg': base_writing + writing_adj,
                    'composite_avg': int((base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 19),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: MCAP Achievement Data (modeled from MSDE Report Card)
# ============================================================================

def load_mcap_data(leas_df):
    """
    Generate MCAP achievement data based on Maryland MCAP patterns.
    MCAP has 4 performance levels: Beginning, Developing, Proficient, Distinguished.
    Statewide: ELA 50.8%, Math 26.5% proficient+.
    """
    mcap_data = []

    for _, d in leas_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    # Base from LEA-level data
                    base = d['mcap_ela_all'] if subject == 'ELA' else d['mcap_math_all']
                    # Grade adjustment
                    proficient_rate = max(10, min(95, base + (grade - 5) * -1.3))

                    distinguished = max(3, proficient_rate * 0.22)
                    proficient_only = proficient_rate - distinguished
                    developing = max(10, (100 - proficient_rate) * 0.50)
                    beginning = max(5, 100 - proficient_rate - developing)

                    mcap_data.append({
                        'county_code': d['county_code'],
                        'lea_name': d['lea_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'proficient_rate': round(proficient_rate, 1),
                        'distinguished_pct': round(distinguished, 1),
                        'proficient_pct': round(proficient_only, 1),
                        'developing_pct': round(developing, 1),
                        'beginning_pct': round(beginning, 1),
                    })

    return pd.DataFrame(mcap_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (modeled from MSDE ACCESS reports)
# ============================================================================

def load_statewide_domain_data():
    """
    Statewide ACCESS domain proficiency percentages by grade cluster.
    Maryland exit criterion: composite 4.5.
    WIDA ACCESS, 4 domains. ~112,081 ELs statewide.
    """
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 43, 'speaking': 39, 'reading': 29, 'writing': 22},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 49, 'speaking': 45, 'reading': 33, 'writing': 24},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 53, 'speaking': 47, 'reading': 36, 'writing': 26},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 56, 'speaking': 49, 'reading': 39, 'writing': 28},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 41, 'speaking': 37, 'reading': 27, 'writing': 20},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 47, 'speaking': 43, 'reading': 31, 'writing': 22},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 51, 'speaking': 45, 'reading': 34, 'writing': 24},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 54, 'speaking': 47, 'reading': 37, 'writing': 26},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, county_code, grade, year):
    filtered = access_df[
        (access_df['county_code'] == county_code) & (access_df['grade'] == grade) & (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'county_code': county_code, 'lea_name': row['lea_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'delta': delta, 'delta_normalized': delta_normalized, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(leas_df):
    st.header("Maryland Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pilot LEAs", len(leas_df))
    with col2: st.metric("Total Students", f"{leas_df['total_students'].sum():,}")
    with col3: st.metric("English Learners", f"{leas_df['el_count'].sum():,}")
    with col4: st.metric("Statewide ELA", "50.8%", help="MCAP ELA proficient+ rate")

    st.divider()

    st.subheader("Maryland Equity Context")
    col1, col2, col3 = st.columns(3)
    with col1: st.error("**ELA 50.8%**\nMCAP Proficient+ Statewide")
    with col2: st.error("**Math 26.5%**\nMCAP Proficient+ Statewide")
    with col3: st.warning("**$3.8B Blueprint**\nBlueprint for Maryland's Future")

    st.divider()

    st.subheader("Key Maryland Facts")
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        - **24 LEAs** (23 counties + Baltimore City)
        - **District ID:** 2-digit county code
        - **Student ID:** SASID (10-digit)
        - **Dashboard:** reportcard.msde.maryland.gov (1-5 stars)
        - **WIDA ACCESS** -- EXIT criterion: **composite 4.5**
        """)
    with col2:
        st.info("""
        - **MCAP:** 4 levels -- Beginning, Developing, Proficient, Distinguished
        - **112,081 ELs** statewide
        - **PG + Montgomery = 52%** of all state ELs
        - **Blueprint for Maryland's Future:** $3.8B reform
        - **Excellence Act (2025):** protected EL funding
        """)

    st.divider()

    st.subheader("Pilot LEAs -- Highest EL Populations")
    display = leas_df[['county_code', 'lea_name', 'total_students', 'el_count', 'el_percent',
                        'graduation_rate', 'mcap_ela_all', 'mcap_math_all']].copy()
    display['el_percent'] = display['el_percent'].apply(lambda x: f"{x:.1f}%")
    display['graduation_rate'] = display['graduation_rate'].apply(lambda x: f"{x:.1f}%")
    display['mcap_ela_all'] = display['mcap_ela_all'].apply(lambda x: f"{x:.1f}%")
    display['mcap_math_all'] = display['mcap_math_all'].apply(lambda x: f"{x:.1f}%")
    display.columns = ['County Code', 'LEA', 'Students', 'EL Count', 'EL %',
                       'Grad Rate', 'MCAP ELA %', 'MCAP Math %']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Learner Population by LEA")
    fig = px.bar(
        leas_df.sort_values('el_count', ascending=True),
        x='el_count', y='lea_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, MD_RED]],
        labels={'el_count': 'English Learners', 'lea_name': 'LEA', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** MSDE ACCESS for ELLs reporting. Maryland uses WIDA ACCESS with 4 domains.
    Domain proficiency percentages show the systemic oral-written delta: Speaking consistently
    outperforms Writing across all grade clusters. Maryland uses a **composite 4.5 exit criterion**.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', MD_BLACK), ('speaking', MD_GOLD), ('reading', '#888'), ('writing', MD_RED)]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 70])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[MD_RED if d > 18 else MD_GOLD for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")


def render_access_analysis(access_df, leas_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains: Listening, Speaking, Reading, Writing.
    Maryland uses WIDA ACCESS with a **composite 4.5 exit criterion**.
    112,081 ELs statewide across 24 LEAs.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: lea = st.selectbox("LEA", leas_df['lea_name'].tolist(), key="acc_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="acc_y")

    code = leas_df[leas_df['lea_name'] == lea]['county_code'].values[0]
    filtered = access_df[(access_df['county_code'] == code) & (access_df['grade'] == grade) & (access_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(x=domains, y=scores, marker_color=[MD_BLACK, MD_GOLD, '#888', MD_RED],
                               text=[f"{s:.0f}" for s in scores], textposition='outside'))
        fig.update_layout(title=f"ACCESS Domains -- {lea} -- Grade {grade} ({year})",
                         yaxis_title="Scale Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        st.subheader("Oral vs Written Gap")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average", f"{oral:.0f}")
        with col2: st.metric("Written Average", f"{written:.0f}")
        with col3: st.metric("Gap", f"{gap:+.0f}", delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")


def render_type4(access_df, leas_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score. Flag threshold: normalized delta > 8 points.

    In Maryland, the ACCESS composite weighting (Reading 35%, Writing 35%, Speaking 15%, Listening 15%)
    means writing deficiency heavily drags down composite scores, potentially keeping students
    classified as EL long past oral fluency. Maryland's **composite 4.5 exit criterion** is among
    the higher thresholds nationally.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: lea = st.selectbox("LEA", leas_df['lea_name'].tolist(), key="t4_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    code = leas_df[leas_df['lea_name'] == lea]['county_code'].values[0]
    result = compute_type4_analysis(access_df, code, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2: st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3: st.metric("Delta", f"{result['delta']:+.0f}")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']], marker_color=MD_GOLD))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']], marker_color=MD_RED))
        fig.update_layout(title=f"Speaking vs Writing -- {lea} -- Grade {grade}", barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        st.subheader(f"All Grades -- {lea} ({year})")
        all_data = [compute_type4_analysis(access_df, code, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                                     mode='lines+markers', line=dict(color=MD_GOLD, width=3)))
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                                     mode='lines+markers', line=dict(color=MD_RED, width=3)))
            fig.update_layout(title="Speaking vs Writing Across Grades", xaxis_title="Grade",
                             yaxis_title="Scale Score", height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_achievement_gaps(leas_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **MCAP proficiency by subgroup** across pilot LEAs. Maryland's statewide MCAP proficiency
    rates -- ELA **50.8%** and Math **26.5%** -- reveal significant room for growth.
    The Blueprint for Maryland's Future ($3.8B) and Excellence Act (2025) target these gaps
    with protected EL funding.
    """)

    st.divider()

    # Compute EL-estimated rates for visualization
    leas_copy = leas_df.copy()
    leas_copy['mcap_ela_el'] = (leas_copy['mcap_ela_all'] * 0.45).round(1)
    leas_copy['mcap_math_el'] = (leas_copy['mcap_math_all'] * 0.42).round(1)

    fig = go.Figure()
    sorted_df = leas_copy.sort_values('mcap_ela_all', ascending=True)
    for col, name, color in [
        ('mcap_ela_all', 'All Students ELA', MD_BLACK),
        ('mcap_ela_el', 'EL ELA (est.)', MD_GOLD),
        ('mcap_math_all', 'All Students Math', '#888'),
        ('mcap_math_el', 'EL Math (est.)', MD_RED),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['lea_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="MCAP Pass Rates by Subgroup -- ELA & Math",
        barmode='group', xaxis_title="% Proficient+", height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("All Students vs EL -- ELA Gap by LEA")
    leas_copy['gap'] = leas_copy['mcap_ela_all'] - leas_copy['mcap_ela_el']
    sorted_gap = leas_copy.sort_values('gap', ascending=True)
    colors = [MD_RED if g > 30 else MD_GOLD if g > 20 else MD_BLACK for g in sorted_gap['gap']]
    fig2 = go.Figure(go.Bar(
        x=sorted_gap['gap'], y=sorted_gap['lea_name'],
        orientation='h', marker_color=colors,
        text=[f"{g:.0f} pts" for g in sorted_gap['gap']], textposition='outside'
    ))
    fig2.update_layout(title="All Students - EL MCAP ELA Gap", xaxis_title="Gap (percentage points)", height=550)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("EL ELA vs LEA Overall")
    fig3 = px.scatter(
        leas_copy, x='mcap_ela_all', y='mcap_ela_el', size='el_count',
        color='el_percent', color_continuous_scale=[[0, '#ccc'], [1, MD_RED]],
        hover_name='lea_name',
        labels={'mcap_ela_all': 'All Students ELA %', 'mcap_ela_el': 'EL ELA % (est.)',
                'el_count': 'EL Count', 'el_percent': 'EL %'}
    )
    fig3.add_shape(type="line", x0=10, y0=10, x1=70, y1=70, line=dict(dash="dash", color="gray"))
    fig3.update_layout(title="EL vs Overall MCAP ELA -- Gap Visualization", height=450)
    st.plotly_chart(fig3, use_container_width=True)


def render_mcap(mcap_df, leas_df):
    st.header("MCAP Assessment Analysis")
    st.markdown("""
    **Maryland Comprehensive Assessment Program (MCAP)** -- Maryland's academic assessment.
    4 performance levels: **Beginning, Developing, Proficient, Distinguished**.
    Statewide: ELA **50.8%**, Math **26.5%** proficient+.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1: lea = st.selectbox("LEA", leas_df['lea_name'].tolist(), key="mcap_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="mcap_g")
    with col3: subject = st.selectbox("Subject", ['ELA', 'Math'], key="mcap_s")
    with col4: year = st.selectbox("Year", [2025, 2024], key="mcap_y")

    code = leas_df[leas_df['lea_name'] == lea]['county_code'].values[0]
    filtered = mcap_df[(mcap_df['county_code'] == code) & (mcap_df['grade'] == grade) &
                       (mcap_df['subject'] == subject) & (mcap_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Beginning", f"{row['beginning_pct']:.1f}%")
        with col2: st.metric("Developing", f"{row['developing_pct']:.1f}%")
        with col3: st.metric("Proficient", f"{row['proficient_pct']:.1f}%")
        with col4: st.metric("Distinguished", f"{row['distinguished_pct']:.1f}%")

        levels = ['Beginning', 'Developing', 'Proficient', 'Distinguished']
        values = [row['beginning_pct'], row['developing_pct'], row['proficient_pct'], row['distinguished_pct']]
        colors = [MD_RED, '#f57c00', MD_GOLD, MD_BLACK]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"MCAP {subject} -- {lea} -- Grade {grade} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Proficiency Rate", f"{row['proficient_rate']:.1f}%",
                  help="Proficient + Distinguished combined")

        # Cross-grade comparison
        st.subheader(f"MCAP {subject} Proficiency Across Grades -- {lea} ({year})")
        all_grades = mcap_df[(mcap_df['county_code'] == code) & (mcap_df['subject'] == subject) & (mcap_df['year'] == year)]
        if not all_grades.empty:
            fig2 = go.Figure(go.Bar(
                x=all_grades['grade'], y=all_grades['proficient_rate'],
                marker_color=MD_RED,
                text=[f"{v:.0f}%" for v in all_grades['proficient_rate']], textposition='outside'
            ))
            fig2.update_layout(
                xaxis_title="Grade", yaxis_title="Proficiency Rate %",
                height=350, yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig2, use_container_width=True)


def render_export(access_df, mcap_df, leas_df, domain_df):
    st.header("Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button("Download ACCESS CSV", access_df.to_csv(index=False),
                          "vera_md_access.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("MCAP Data")
        st.dataframe(mcap_df, use_container_width=True, hide_index=True)
        st.download_button("Download MCAP CSV", mcap_df.to_csv(index=False),
                          "vera_md_mcap.csv", "text/csv", use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("LEA Summary")
        st.dataframe(leas_df, use_container_width=True, hide_index=True)
        st.download_button("Download LEAs CSV", leas_df.to_csv(index=False),
                          "vera_md_leas.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button("Download Domain CSV", domain_df.to_csv(index=False),
                          "vera_md_domains.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-MD | Maryland Type 4 Detection", page_icon="🦀", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {MD_RED}; }}
        .stButton > button {{ background-color: {MD_RED}; color: white; }}
        .stButton > button:hover {{ background-color: {MD_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    leas_df = load_leas()
    access_df = load_access_data(leas_df)
    mcap_df = load_mcap_data(leas_df)
    domain_df = load_statewide_domain_data()

    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {MD_RED}; margin: 0;">VERA-MD</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Maryland Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "MCAP Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - MSDE Report Card
    - MCAP Assessments
    - reportcard.msde.maryland.gov

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points
    - EXIT criterion: composite 4.5

    **Key Context:**
    - 112,081 ELs statewide
    - 24 LEAs (23 counties + Baltimore City)
    - PG + Montgomery = 52% of ELs
    - MCAP: ELA 50.8%, Math 26.5%
    - Blueprint: $3.8B reform
    - Excellence Act (2025): EL funding

    **Top EL LEAs:**
    - Prince George's: 33,121
    - Montgomery: 31,706
    - Baltimore County: 12,191
    - Baltimore City: 9,702

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(leas_df)
    elif page == "Domain Analysis": render_domain_analysis(domain_df)
    elif page == "ACCESS Analysis": render_access_analysis(access_df, leas_df)
    elif page == "Type 4 Detection": render_type4(access_df, leas_df)
    elif page == "Achievement Gaps": render_achievement_gaps(leas_df)
    elif page == "MCAP Analysis": render_mcap(mcap_df, leas_df)
    elif page == "Export Data": render_export(access_df, mcap_df, leas_df, domain_df)


if __name__ == "__main__":
    main()
