"""
utils/plot_builders.py
======================
Pure Plotly figure builders.  Zero Dash / callback imports.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_centerline_concentration_plot(X, Y, concentration, wind_dir=45):
    """Centerline concentration profile (semi-log)."""
    ny, nx = X.shape
    centerline_idx = ny // 2
    centerline_conc = concentration[centerline_idx, :]
    downwind_dist = X[centerline_idx, :]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=downwind_dist,
        y=centerline_conc,
        mode='lines',
        name='Centerline Concentration',
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.15)',
        hovertemplate='<b>Distance:</b> %{x:.1f} m<br><b>Concentration:</b> %{y:.2f} ppm<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='<b>Centerline Concentration Profile</b>', font=dict(size=16, color='#1f77b4')),
        xaxis=dict(title='<b>Downwind Distance (m)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)'),
        yaxis=dict(title='<b>Concentration (ppm)</b>', type='log', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)'),
        template='plotly_white',
        height=450,
        hovermode='x unified',
        margin=dict(l=70, r=40, t=80, b=70),
        font=dict(family='Arial, sans-serif', size=11),
        plot_bgcolor='rgba(240,240,245,0.5)',
        paper_bgcolor='white',
    )
    return fig


def create_crosswind_concentration_plot(X, Y, concentration):
    """Crosswind concentration profiles at 25 / 50 / 75 % of the domain."""
    max_downwind = np.nanmax(X)
    downwind_distances = [max_downwind * 0.25, max_downwind * 0.50, max_downwind * 0.75]

    fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    fill_colors = [
        'rgba(31, 119, 180, 0.15)',
        'rgba(255, 127, 14, 0.15)',
        'rgba(44, 160, 44, 0.15)',
    ]

    for i, target_dist in enumerate(downwind_distances):
        x_row = X[0, :]
        closest_idx = np.argmin(np.abs(x_row - target_dist))
        actual_dist = x_row[closest_idx]
        crosswind_conc = concentration[:, closest_idx]
        y_vals = Y[:, closest_idx]

        fig.add_trace(go.Scatter(
            x=y_vals,
            y=crosswind_conc,
            mode='lines',
            name=f'{actual_dist:.0f}m Downwind',
            line=dict(color=colors[i], width=2.5),
            fill='tozeroy',
            fillcolor=fill_colors[i],
            hovertemplate=(
                '<b>Crosswind:</b> %{x:.1f} m<br>'
                '<b>Concentration:</b> %{y:.2f} ppm<extra></extra>'
            ),
        ))

    fig.update_layout(
        title=dict(text='<b>Crosswind Concentration Profiles</b>', font=dict(size=16, color='#1f77b4')),
        xaxis=dict(title='<b>Crosswind Distance (m)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)'),
        yaxis=dict(title='<b>Concentration (ppm)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)'),
        template='plotly_white',
        height=450,
        hovermode='x unified',
        margin=dict(l=70, r=40, t=80, b=70),
        font=dict(family='Arial, sans-serif', size=11),
        plot_bgcolor='rgba(240,240,245,0.5)',
        paper_bgcolor='white',
        legend=dict(x=0.70, y=0.95, bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='#ccc', borderwidth=1),
    )
    return fig


def create_concentration_contour_plot(X, Y, concentration, thresholds, wind_dir=45):
    """2-D spatial contour / heatmap with AEGL zone overlays."""
    fig = go.Figure()

    min_threshold = min(thresholds.values()) if thresholds else 1.0
    significant_mask = concentration >= (min_threshold * 0.1)

    if np.any(significant_mask):
        y_indices, x_indices = np.where(significant_mask)
        x_min_idx, x_max_idx = np.min(x_indices), np.max(x_indices)
        y_min_idx, y_max_idx = np.min(y_indices), np.max(y_indices)
        x_vals = X[0, :]
        y_vals = Y[:, 0]
        x_min, x_max = x_vals[x_min_idx], x_vals[x_max_idx]
        y_min, y_max = y_vals[y_min_idx], y_vals[y_max_idx]
        xp = (x_max - x_min) * 0.15
        yp = (y_max - y_min) * 0.15
        x_range = [x_min - xp, x_max + xp]
        y_range = [y_min - yp, y_max + yp]
    else:
        x_range = [np.nanmin(X), np.nanmax(X)]
        y_range = [np.nanmin(Y), np.nanmax(Y)]

    aegl_thresholds = {
        'AEGL-1': thresholds.get('AEGL-1', 30),
        'AEGL-2': thresholds.get('AEGL-2', 160),
        'AEGL-3': thresholds.get('AEGL-3', 1100),
    }
    max_conc = float(np.nanmax(concentration)) + 100
    aegl1_norm = float(min(aegl_thresholds['AEGL-1'] / max_conc, 0.99))
    aegl2_norm = float(min(aegl_thresholds['AEGL-2'] / max_conc, 0.995))
    aegl3_norm = float(min(aegl_thresholds['AEGL-3'] / max_conc, 1.0))

    custom_colorscale = [
        [0.0,        'rgb(0, 0, 131)'],
        [aegl1_norm, 'rgb(255, 215, 0)'],
        [aegl2_norm, 'rgb(255, 165, 0)'],
        [aegl3_norm, 'rgb(255, 0, 0)'],
        [1.0,        'rgb(139, 0, 0)'],
    ]

    fig.add_trace(go.Contour(
        x=X[0, :], y=Y[:, 0], z=concentration,
        colorscale=custom_colorscale,
        colorbar=dict(title=dict(text='<b>Conc<br>(ppm)</b>', font=dict(size=12)),
                      thickness=20, len=0.8, tickfont=dict(size=11), x=1.02),
        name='Concentration',
        contours=dict(coloring='heatmap', showlabels=False),
        hovertemplate='<b>X:</b> %{x:.0f}m<br><b>Y:</b> %{y:.0f}m<br><b>Conc:</b> %{z:.1f}ppm<extra></extra>',
    ))

    colors_map = {
        'AEGL-1': 'rgb(255, 215, 0)',
        'AEGL-2': 'rgb(255, 165, 0)',
        'AEGL-3': 'rgb(255, 0, 0)',
    }
    for name, val in sorted(aegl_thresholds.items(), key=lambda kv: kv[1], reverse=True):
        fig.add_trace(go.Contour(
            x=X[0, :], y=Y[:, 0], z=concentration,
            contours=dict(type='constraint', operation='>=', value=val, showlabels=False),
            line=dict(color=colors_map.get(name, '#999'), width=2.5),
            name=f'{name} (≥{val:.0f} ppm)',
            showscale=False,
            hovertemplate=f'<b>{name}</b><br>≥{val:.0f} ppm<extra></extra>',
        ))

    fig.update_layout(
        title=dict(text='<b>Concentration Distribution (2D Spatial Map)</b>',
                   font=dict(size=16, color='#1f77b4')),
        xaxis=dict(title='<b>Downwind Distance (m)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)', range=x_range),
        yaxis=dict(title='<b>Crosswind Distance (m)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)', range=y_range,
                   scaleanchor='x', scaleratio=1),
        template='plotly_white',
        height=650,
        autosize=True,
        margin=dict(l=70, r=180, t=80, b=70),
        font=dict(family='Arial, sans-serif', size=11),
        plot_bgcolor='rgba(240,240,245,0.3)',
        paper_bgcolor='white',
        legend=dict(x=1.05, y=0.95, bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='#ccc', borderwidth=1),
        hovermode='closest',
    )
    fig.add_annotation(
        text=f'Wind Dir: {wind_dir:.0f}°',
        xref='paper', yref='paper', x=0.02, y=0.98,
        showarrow=False,
        bgcolor='rgba(255,255,255,0.9)', bordercolor='#555', borderwidth=1.5,
        font=dict(size=11, color='#333'),
    )
    return fig


def create_concentration_statistics(concentration, thresholds):
    """Bar-chart subplots: concentration statistics + area-above-AEGL."""
    non_zero = concentration[concentration > 0]

    stats_dict = {
        'Maximum':   float(np.nanmax(concentration)),
        'Mean':      float(np.nanmean(non_zero)) if len(non_zero) > 0 else 0.0,
        'Median':    float(np.nanmedian(non_zero)) if len(non_zero) > 0 else 0.0,
        '95th %ile': float(np.nanpercentile(non_zero, 95)) if len(non_zero) > 0 else 0.0,
        '75th %ile': float(np.nanpercentile(non_zero, 75)) if len(non_zero) > 0 else 0.0,
    }

    total_pixels = concentration.size
    affected_areas = {
        name: (np.sum(concentration >= thresh) / total_pixels) * 100
        for name, thresh in thresholds.items()
    }

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'bar'}, {'type': 'bar'}]],
        subplot_titles=(
            '<b>Concentration Statistics (ppm)</b>',
            '<b>Area Above AEGL Thresholds (%)</b>',
        ),
        horizontal_spacing=0.15,
    )
    fig.add_trace(go.Bar(
        x=list(stats_dict.keys()), y=list(stats_dict.values()),
        marker=dict(color=['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd'],
                    line=dict(color='#333', width=1.5)),
        text=[f'{v:.1f}' for v in stats_dict.values()], textposition='outside',
        textfont=dict(size=10, color='#333'), showlegend=False, name='Statistics',
        hovertemplate='<b>%{x}</b><br>Value: %{y:.2f} ppm<extra></extra>',
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=list(affected_areas.keys()), y=list(affected_areas.values()),
        marker=dict(color=['#FF0000', '#FFA500', '#FFFF00'],
                    line=dict(color='#333', width=1.5)),
        text=[f'{v:.2f}%' for v in affected_areas.values()], textposition='outside',
        textfont=dict(size=10, color='#333'), showlegend=False, name='Affected Area',
        hovertemplate='<b>%{x}</b><br>Area: %{y:.2f}%<extra></extra>',
    ), row=1, col=2)

    fig.update_yaxes(title_text='<b>Concentration (ppm)</b>', row=1, col=1,
                     showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
    fig.update_yaxes(title_text='<b>Affected Area (%)</b>', row=1, col=2,
                     showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
    fig.update_xaxes(tickangle=-45, row=1, col=1)
    fig.update_xaxes(tickangle=-45, row=1, col=2)
    fig.update_layout(
        title=dict(text='<b>Concentration & Impact Area Analysis</b>',
                   font=dict(size=16, color='#1f77b4')),
        template='plotly_white', height=450, showlegend=False,
        margin=dict(l=70, r=40, t=80, b=100),
        font=dict(family='Arial, sans-serif', size=11),
        plot_bgcolor='rgba(240,240,245,0.5)', paper_bgcolor='white',
    )
    return fig


def create_distance_vs_concentration_plot(X, Y, concentration, thresholds):
    """Line plot: max concentration vs downwind distance (log-y)."""
    downwind_dist = X[0, :]
    max_conc_by_dist = np.nanmax(concentration, axis=0)
    max_conc = float(np.nanmax(max_conc_by_dist))
    positive = max_conc_by_dist[max_conc_by_dist > 0]
    min_conc = float(np.nanmin(positive)) if len(positive) > 0 else 0.1

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=downwind_dist,
        y=max_conc_by_dist,
        mode='lines+markers',
        name='Max Concentration',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=5),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.15)',
        hovertemplate=(
            '<b>Distance:</b> %{x:.1f} m<br>'
            '<b>Max Conc:</b> %{y:.2f} ppm<extra></extra>'
        ),
    ))

    colors_map = {'AEGL-1': '#FFFF00', 'AEGL-2': '#FFA500', 'AEGL-3': '#FF0000'}
    for name, threshold in sorted(thresholds.items(), key=lambda kv: kv[1]):
        fig.add_hline(
            y=threshold, line_dash='dash',
            line_color=colors_map.get(name, '#999'), line_width=2,
            annotation_text=f'<b>{name}</b><br>({threshold:.0f} ppm)',
            annotation_position='right',
            annotation_font_size=10, annotation_font_color='#333',
        )

    y_min = min_conc / 10
    y_max = max_conc * 10
    fig.update_layout(
        title=dict(text='<b>Maximum Concentration vs. Downwind Distance</b>',
                   font=dict(size=16, color='#1f77b4')),
        xaxis=dict(title='<b>Downwind Distance (m)</b>', showgrid=True, gridwidth=1,
                   gridcolor='rgba(200,200,200,0.2)'),
        yaxis=dict(
            title='<b>Maximum Concentration (ppm)</b>', type='log',
            range=[np.log10(y_min), np.log10(y_max)],
            showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)',
        ),
        template='plotly_white', height=450, hovermode='x unified',
        margin=dict(l=70, r=220, t=80, b=70),
        font=dict(family='Arial, sans-serif', size=11),
        plot_bgcolor='rgba(240,240,245,0.5)', paper_bgcolor='white',
    )
    return fig
