"""
Parser comparison script for local use.
This script lets you visualize side-by-side how each parser analyzes a document, and compare the resulting tables.
"""

# Bootstrap and common imports
import sys, os, time, textwrap
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Configure matplotlib for compact, high-quality output
plt.rcParams.update({
    'figure.dpi': 120,
    'savefig.dpi': 200,
    'font.size': 8,
    'axes.titlesize': 10,
    'axes.labelsize': 8,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 7,
    'figure.titlesize': 10,
    'image.interpolation': 'bilinear',
    'image.resample': True,
})

sys.path.insert(
    0, os.path.abspath("")
)  # Prefer the local version of camelot if available
import camelot

print(f"Using camelot v{camelot.__version__}.")

# Select a PDF file to review
# Modify the filename below to point to your PDF file
KWARGS = {}
DATA = None

FILENAME = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"
# Specify which pages to parse (e.g., "1", "1,2,5", "1-3,5")

PAGES_TO_PARSE = "15"  # Change this string to select custom pages

# Parse page ranges and individual pages
def parse_page_string(pages_str):
    """Parse page string like '1-19', '1,3,5', '1-3,5-7' into list of page numbers."""
    pages = []
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return [str(p) for p in pages]

page_list = parse_page_string(PAGES_TO_PARSE)

FLAVORS = ["stream", "lattice", "network", "hybrid"]
FLAVORS = ["lattice"]

# Configuration for window display
# Set how many pages to show side by side in each window (1 row, N columns)
PAGES_PER_WINDOW = 3  # Change this value to control how many pages per window

def plot_parsing_report_as_image(parsing_report, ax, title="Parsing Report"):
    """Display parsing report as formatted text in an image."""
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Format the parsing report
    if isinstance(parsing_report, dict):
        report_text = ""
        for key, value in parsing_report.items():
            if isinstance(value, (int, float)):
                report_text += f"{key}: {value:.3f}\n"
            else:
                report_text += f"{key}: {value}\n"
    else:
        report_text = str(parsing_report)

    # Wrap text to fit in the display area with more width
    wrapped_text = textwrap.fill(report_text, width=80)

    # Add background rectangle with better styling
    rect = Rectangle((0.01, 0.01), 0.98, 0.98,
                    linewidth=1.5, edgecolor='darkgray',
                    facecolor='lightgray', alpha=0.15)
    ax.add_patch(rect)

    # Add text with better formatting - smaller font for more content
    ax.text(0.05, 0.95, title, fontsize=11, fontweight='bold',
           verticalalignment='top', transform=ax.transAxes,
           color='darkblue')
    ax.text(0.05, 0.85, wrapped_text, fontsize=8,
           verticalalignment='top', transform=ax.transAxes,
           fontfamily='monospace', linespacing=1.1)


def plot_page(page_num, parses, max_tables):
    """Plot a single page with table detection and parsing reports."""
    # New layout: tables in a grid, parsing report as a wide text area at the bottom
    n_flavors = len(FLAVORS)
    n_tables = max(max_tables, 1)
    table_rows = n_tables
    table_cols = n_flavors
    report_height_ratio = 0.18  # Fraction of figure height for reports
    table_height_ratio = 1 - report_height_ratio

    # Make pages as big as possible
    fig_width = 18 * table_cols  # much larger width
    fig_height = 22 * table_rows  # much larger height
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=150)
    fig.suptitle(f"Page {page_num} - Tables & Parsing Reports", fontsize=20, fontweight="bold")

    # Table axes grid
    table_axes = []
    for row in range(table_rows):
        row_axes = []
        for col in range(table_cols):
            left = col / table_cols
            bottom = 1 - ((row + 1) * table_height_ratio / table_rows)
            width = 1 / table_cols
            height = table_height_ratio / table_rows
            ax = fig.add_axes((left + 0.01, bottom + 0.01, width - 0.02, height - 0.02))
            row_axes.append(ax)
        table_axes.append(row_axes)

    # Parsing report axes (one per flavor, horizontally aligned at bottom)
    report_axes = []
    for col in range(table_cols):
        left = col / table_cols
        bottom = 0.01
        # Make the width smaller to create a more compact box
        width = (1 / table_cols) * 0.8  # Reduced to 80% of original width
        height = report_height_ratio - 0.015
        # Center the box by adjusting the left position
        left_adjusted = left + ((1 / table_cols) - width) / 2
        ax = fig.add_axes((left_adjusted, bottom, width, height))
        report_axes.append(ax)

    # Plot tables
    for flavor_idx, flavor in enumerate(FLAVORS):
        parse = parses[flavor]
        tables = parse["tables"]
        for table_idx in range(table_rows):
            ax = table_axes[table_idx][flavor_idx]
            if table_idx < len(tables):
                table = tables[table_idx]
                if table.shape[0] > 0 and table.shape[1] > 0:
                    camelot.plot(table, kind="grid", ax=ax)
                    ax.set_title(f"{flavor} Table {table_idx}\n{table.shape[0]}x{table.shape[1]}", fontsize=16, fontweight="bold")
                    for line in ax.lines:
                        line.set_linewidth(2.0)
                        line.set_antialiased(True)
                else:
                    ax.text(0.5, 0.5, "Empty Table", ha='center', va='center', transform=ax.transAxes, fontsize=16)
                    ax.set_title(f"{flavor} Table {table_idx} (Empty)", fontsize=15)
            else:
                ax.axis('off')

    # Plot parsing reports at the bottom, one per flavor, covering all tables
    for flavor_idx, flavor in enumerate(FLAVORS):
        parse = parses[flavor]
        # Combine all parsing reports for this flavor into one text
        report_text = ""
        for table_idx, table in enumerate(parse["tables"]):
            report_text += f"Table {table_idx}:\n"
            if hasattr(table, 'parsing_report'):
                if isinstance(table.parsing_report, dict):
                    for k, v in table.parsing_report.items():
                        report_text += f"  {k}: {v}\n"
                else:
                    report_text += f"  {table.parsing_report}\n"
            else:
                report_text += "  No parsing report.\n"
            report_text += "\n"
        # Add error if present
        if parse.get("error"):
            report_text += f"Error: {parse['error']}\n"
        # Add timing
        report_text += f"Parse time: {parse['time']:.3f} sec\n"
        # Plot as text at the bottom
        ax = report_axes[flavor_idx]
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        wrapped_text = textwrap.fill(report_text, width=120)
        rect = Rectangle((0.01, 0.01), 0.98, 0.98, linewidth=1.5, edgecolor='darkgray', facecolor='lightgray', alpha=0.15)
        ax.add_patch(rect)
        ax.text(0.02, 0.98, f"{flavor} Parsing Report", fontsize=25, fontweight='bold', verticalalignment='top', transform=ax.transAxes, color='darkblue')
        ax.text(0.02, 0.90, wrapped_text, fontsize=20, verticalalignment='top', transform=ax.transAxes, fontfamily='monospace', linespacing=1.0)

    return fig


def create_window_with_pages(pages_data, window_num):
    """Create a window showing multiple pages with appropriate scaling."""
    num_pages = len(pages_data)
    fig_width = 5 * num_pages  # Reduce width per page for tighter layout
    fig_height = 7  # Reduce height for a more compact display

    window_fig, axes = plt.subplots(1, num_pages, figsize=(fig_width, fig_height), dpi=150)
    # Ensure axes is always a flat list for consistent indexing
    if isinstance(axes, np.ndarray):
        axes = list(axes.flat)
    else:
        axes = [axes]
    window_fig.suptitle(f"Window {window_num} - Pages {pages_data[0]['page']} to {pages_data[-1]['page']}", 
                        fontsize=15, fontweight="bold")

    # Remove all spacing between subplots
    plt.subplots_adjust(left=0, right=1, top=0.92, bottom=0, wspace=0, hspace=0)

    for idx, page_data in enumerate(pages_data):
        ax = axes[idx]
        # Create the individual page plot
        page_fig = plot_page(page_data['page'], page_data['parses'], page_data['max_tables'])
        page_fig.canvas.draw()
        # Use the correct canvas for tostring_rgb
        canvas = page_fig.canvas
        buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
        width, height = canvas.get_width_height()
        buf = buf.reshape((height, width, 3))
        ax.imshow(buf, interpolation='bilinear', aspect='auto')
        ax.set_title(f"Page {page_data['page']}", fontsize=14, fontweight="bold")
        ax.axis('off')
        plt.close(page_fig)

    return window_fig

pages_data = []  # Store all page data here

for page in page_list:
    print(f"\n=== Processing page {page} ===")
    tables_parsed = {}
    parses = {}
    max_tables = 0
    
    for flavor_idx, flavor in enumerate(FLAVORS):
        timer_before_parse = time.perf_counter()
        error, tables = None, []
        try:
            tables = camelot.read_pdf(FILENAME, flavor=flavor, debug=True, 
                                    pages=page, **KWARGS)
        except ValueError as value_error:
            error = f"Invalid argument for parser {flavor}: {value_error}"
            print(error)
        timer_after_parse = time.perf_counter()
        max_tables = max(max_tables, len(tables))

        parses[flavor] = {
            "tables": tables,
            "time": timer_after_parse - timer_before_parse,
            "error": error,
        }

        print(f"##### {flavor} ####")
        print(f"Found {len(tables)} table(s):")
        for table_idx, table in enumerate(tables):
            flavors_matching = []
            
            for previous_flavor, previous_tables in tables_parsed.items():
                for prev_idx, previous_table in enumerate(previous_tables):
                    if previous_table.df.equals(table.df):
                        flavors_matching.append(f"{previous_flavor} table {prev_idx}")
            print(f"## Table {table_idx} ##")
            print("Parsing report: ", table.parsing_report)
            if flavors_matching:
                print(f"Same as {', '.join(flavors_matching)}.")
            else:
                print(table.df)
        tables_parsed[flavor] = tables

    # Store page data instead of creating figure immediately
    pages_data.append({
        'page': page,
        'parses': parses,
        'max_tables': max_tables
    })

# Create and display windows with page images and parsing reports

total_windows = (len(pages_data) + PAGES_PER_WINDOW - 1) // PAGES_PER_WINDOW
print(f"\n=== Total pages: {len(pages_data)}, Creating {total_windows} window(s) ===")

window_figures = []
for i in range(0, len(pages_data), PAGES_PER_WINDOW):
    window_pages = pages_data[i:i + PAGES_PER_WINDOW]
    window_num = (i // PAGES_PER_WINDOW) + 1
    print(f"Creating Window {window_num} with pages {[p['page'] for p in window_pages]}")
    window_fig = create_window_with_pages(window_pages, window_num)
    window_figures.append(window_fig)

print(f"\n=== Created {len(window_figures)} separate window(s) ===")
print("All windows should now be visible with high-resolution page images and parsing reports.")

plt.show(block=True)


