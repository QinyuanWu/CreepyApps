import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import re

# This script plots three graphs from the exported JSON logs of the iOS App Privacy Report:
# - Access Timelapse
# - Percentage of Access by App Identifier
# - Percentage of Access by Sensor Category

# Path to data file
filename = 'YOUR_FILE_NAME'
data_file = 'PATH_TO_YOUR_LOG_FILE' + filename + '.ndjson'

# Read data from file
with open(data_file, 'r') as f:
    # Assuming each line in the file is a JSON record
    data_strings = f.readlines()

# Remove any whitespace characters like `\n` at the end of each line
data_strings = [line.strip() for line in data_strings if line.strip()]

# Parse JSON data
records = [json.loads(s) for s in data_strings]

# Build access events per app and category
app_category_events = {}  # key: (app_id, category), value: list of timestamps

# Initialize counters for pie charts
category_counts = {}
app_counts = {}

for record in records:
    if 'accessor' in record:
        app_id = record['accessor']['identifier']
        category = record['category']
        timestamp_str = record['timeStamp']
        # Parse timestamp
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        key = (app_id, category)
        if key not in app_category_events:
            app_category_events[key] = []
        app_category_events[key].append(timestamp)

        # Update counts for pie charts
        # Count accesses by category
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1

        # Count accesses by app identifier
        if app_id in app_counts:
            app_counts[app_id] += 1
        else:
            app_counts[app_id] = 1

# Map categories to y positions
categories = sorted(set(category for _, category in app_category_events.keys()))
category_to_y = {cat: idx for idx, cat in enumerate(categories)}

# Map apps to colors
apps = sorted(set(app_id for app_id, _ in app_category_events.keys()))
app_to_color = {app: plt.cm.tab10(idx % 10) for idx, app in enumerate(apps)}

# Collect all times for setting x-axis limits
all_times = []
for timestamps in app_category_events.values():
    all_times.extend(timestamps)
min_time = min(all_times)
max_time = max(all_times)

# Now plot the graph with smaller dots
fig1, ax1 = plt.subplots(figsize=(16, 6))

plotted_apps = set()

for (app_id, category), timestamps in app_category_events.items():
    color = app_to_color[app_id]
    y = category_to_y[category]
    times = mdates.date2num(timestamps)
    y_values = [y] * len(times)
    label = app_id if app_id not in plotted_apps else ""
    ax1.plot(times, y_values, 'o', color=color, label=label, markersize=4)
    plotted_apps.add(app_id)

# Set y-axis labels
ax1.set_yticks(range(len(categories)))
ax1.set_yticklabels(categories)

# Format x-axis
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))

# Reduce the number of x-axis ticks
ax1.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))

# Rotate x-axis labels
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Ensure x-axis is proportional to the amount of time passed
ax1.set_xlim(mdates.date2num(min_time), mdates.date2num(max_time))

# Adjust layout to prevent clipping
fig1.tight_layout(rect=[0, 0, 0.85, 1])

# Add legend outside the plot area
handles, labels = ax1.get_legend_handles_labels()
if handles:
    # Create a custom legend
    legend = ax1.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5), borderaxespad=0)
    # Adjust font size if necessary
    for text in legend.get_texts():
        text.set_fontsize('small')

# Add title to first graph
title1 = filename + ' Access Timelapse'
plt.title(title1)

# Save the first figure
def sanitize_filename_and_save(title, fig):
    # Remove invalid filename characters
    filename = re.sub(r'[\\/:"*?<>|]+', '_', title) + '.png'
    fig.savefig(os.path.join(os.path.dirname(data_file), filename), dpi=300, bbox_inches='tight')

sanitize_filename_and_save(title1, fig1)

# Now plot the pie charts

# Function to plot pie chart with custom labeling
def plot_pie_chart(data_dict, title):
    labels = list(data_dict.keys())
    sizes = list(data_dict.values())

    # Calculate percentages
    total = sum(sizes)
    percentages = [(s / total) * 100 for s in sizes]

    # Sort the data by size
    sizes, labels, percentages = zip(*sorted(zip(sizes, labels, percentages), reverse=True))

    # Create a function to label only slices >=1%
    def autopct_generator(limit):
        def inner_autopct(pct):
            return ('%1.1f%%' % pct) if pct >= limit else ''
        return inner_autopct

    # Increase the figure width to accommodate the legend
    fig, ax = plt.subplots(figsize=(10, 8))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,  # Don't use labels here to prevent overlap
        autopct=autopct_generator(1),  # Label only slices >=1%
        startangle=140,
        textprops={'fontsize': 8}
    )
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title)

    # Create a legend with all labels and percentages
    legend_labels = []
    for label, pct in zip(labels, percentages):
        if pct >= 1:
            legend_labels.append(f'{label} ({pct:.1f}%)')
        else:
            legend_labels.append(f'{label} (<1%)')

    # Add legend outside the pie chart
    ax.legend(
        wedges,
        legend_labels,
        title='Categories',
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize='small',
        borderaxespad=0
    )

    # Adjust the subplot parameters to make room for the legend
    fig.subplots_adjust(left=0.1, right=0.7)

    return fig, ax  # Return the figure and axes

title2 = filename + ' Percentage of Accesses by Category'
title3 = filename + ' Percentage of Accesses by App Identifier'

# Plot pie chart for accesses by category
fig2, ax2 = plot_pie_chart(category_counts, title2)

# Plot pie chart for accesses by App Identifier
fig3, ax3 = plot_pie_chart(app_counts, title3)

sanitize_filename_and_save(title2, fig2)
sanitize_filename_and_save(title3, fig3)

# Show all plots at once
plt.show()
