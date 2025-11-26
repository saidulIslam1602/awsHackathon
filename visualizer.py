import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

def create_data_map(data_map: Dict) -> go.Figure:
    """Create interactive data collection visualization"""
    
    # Prepare data for sunburst chart
    labels = ["Data Collection"]
    parents = [""]
    values = [0]
    colors = []
    
    color_scheme = {
        "Personal": "#FF6B6B",
        "Behavioral": "#FFA500", 
        "Technical": "#4ECDC4",
        "Social": "#95E1D3"
    }
    
    for category, items in data_map.items():
        labels.append(category)
        parents.append("Data Collection")
        values.append(len(items))
        colors.append(color_scheme.get(category, "#CCCCCC"))
        
        for item in items:
            labels.append(item)
            parents.append(category)
            values.append(1)
            colors.append(color_scheme.get(category, "#CCCCCC"))
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        hovertemplate='<b>%{label}</b><br>Items: %{value}<extra></extra>',
    ))
    
    fig.update_layout(
        title="Data Collection Breakdown",
        height=600,
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig

def create_comparison_chart(comparison_data: Dict) -> go.Figure:
    """Create platform comparison chart"""
    
    platforms = list(comparison_data.keys())
    scores = [comparison_data[p]['score'] for p in platforms]
    data_counts = [comparison_data[p]['data_count'] for p in platforms]
    
    fig = go.Figure()
    
    # Privacy scores
    fig.add_trace(go.Bar(
        name='Privacy Score',
        x=platforms,
        y=scores,
        marker_color='#4ECDC4',
        text=scores,
        textposition='auto',
    ))
    
    # Data collection count
    fig.add_trace(go.Bar(
        name='Data Types Collected',
        x=platforms,
        y=data_counts,
        marker_color='#FF6B6B',
        text=data_counts,
        textposition='auto',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Platform Privacy Comparison',
        xaxis=dict(title='Platform'),
        yaxis=dict(
            title='Privacy Score (0-100)',
            titlefont=dict(color='#4ECDC4'),
            tickfont=dict(color='#4ECDC4')
        ),
        yaxis2=dict(
            title='Data Types Collected',
            titlefont=dict(color='#FF6B6B'),
            tickfont=dict(color='#FF6B6B'),
            overlaying='y',
            side='right'
        ),
        barmode='group',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_privacy_timeline() -> go.Figure:
    """Create timeline showing privacy evolution"""
    years = [2010, 2015, 2018, 2020, 2022, 2024]
    data_points = [50, 150, 500, 1200, 2500, 3000]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=data_points,
        mode='lines+markers',
        name='Data Points Collected Daily',
        line=dict(color='#FF6B6B', width=4),
        marker=dict(size=10, color='#FF6B6B')
    ))
    
    # Add annotations for key events
    annotations = [
        dict(x=2018, y=500, text="GDPR<br>Enacted", showarrow=True, arrowhead=2),
        dict(x=2020, y=1200, text="COVID<br>Digital Surge", showarrow=True, arrowhead=2),
        dict(x=2024, y=3000, text="AI Era<br>Begins", showarrow=True, arrowhead=2)
    ]
    
    fig.update_layout(
        title="📈 The Privacy Crisis: Data Collection Over Time",
        xaxis_title="Year",
        yaxis_title="Average Data Points Collected Per Person Per Day",
        annotations=annotations,
        height=400,
        showlegend=False
    )
    
    return fig

def create_data_flow_sankey(platform_data: Dict) -> go.Figure:
    """Create Sankey diagram showing data flow"""
    
    # Simplified data flow for demo
    labels = [
        "Your Device", "App Collection", "Company Servers", 
        "Advertising Partners", "Analytics Companies", "Government Requests",
        "Data Brokers", "Third-party Apps"
    ]
    
    source = [0, 1, 1, 2, 2, 2, 2, 2]
    target = [1, 2, 2, 3, 4, 5, 6, 7]
    values = [100, 80, 20, 60, 40, 10, 30, 25]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#4ECDC4", "#FF6B6B", "#FFA500", "#FF6B6B", "#FF6B6B", 
                   "#FF6B6B", "#FF6B6B", "#FF6B6B"]
        ),
        link=dict(
            source=source,
            target=target,
            value=values,
            color=["rgba(255, 107, 107, 0.4)"] * len(source)
        )
    )])
    
    fig.update_layout(
        title="🌊 Where Your Data Goes",
        height=500,
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig

def create_risk_gauge(risk_score: int) -> go.Figure:
    """Create gauge chart for privacy risk"""
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Privacy Risk Score"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "#4ECDC4"},
                {'range': [30, 70], 'color': "#FFA500"},
                {'range': [70, 100], 'color': "#FF6B6B"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig
