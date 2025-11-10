def format_heatmap_cell(x, ticker):
        """Formats the cell content to show Ticker and Return (HTML)."""
        if pd.isna(x):
            return ""
        
        # Get the ticker symbol, defaulting to the column name for indices
        symbol = ticker
        
        # Determine text color based on value for better readability
        if abs(x) > 2.0:
            text_color = '#FFFFFF'  # White for strong moves
        else:
            text_color = 'rgba(255, 255, 255, 0.95)'  # Slightly dimmed white
        
        return f"""
        <div class="heatmap-cell" style="color: {text_color};">
            <span class="heatmap-ticker">{symbol}</span>
            <span class="heatmap-return">{x:+.2f}%</span>
        </div>
        """
