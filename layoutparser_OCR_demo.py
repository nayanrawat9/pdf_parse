import layoutparser as lp

import matplotlib.pyplot as plt


import pandas as pd
import numpy as np
import cv2

ocr_agent = lp.TesseractAgent(languages='eng')

filename = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"

# load the pdf
import fitz
doc = fitz.open(filename)
# get the first page
page = doc[4]

# Render the page at higher resolution (e.g., 2x)
zoom_x = 3.0  # horizontal zoom
zoom_y = 3.0  # vertical zoom
mat = fitz.Matrix(zoom_x, zoom_y)
image = page.get_pixmap(matrix=mat)
# save the high-res image
image.save("page.png")

image = cv2.imread('page.png')
# Convert BGR to RGB for correct display in matplotlib
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
# Show image
#plt.imshow(image_rgb)
#plt.axis('off')  # Optional: Hide axes
#plt.show()

res = ocr_agent.detect(image, return_response=True)
#print res
print("res=",res)

## Parse the OCR output and visualize the layout

layout = ocr_agent.gather_data(res, agg_level=lp.TesseractFeatureType.WORD)
    # collect all the layout elements of the `WORD` level
# Gather all the text data into a list
texts = [b.text for b in layout]

# Custom visualization: show detected layout with text and red boxes on left, original image on right

import matplotlib.patches as patches

fig, axes = plt.subplots(1, 2, figsize=(18, 12))

# Left: Detected layout with text and red bounding boxes
axes[0].imshow(image_rgb)
axes[0].set_title("Detected Layout with Text")
axes[0].axis('off')

for block in layout:
    x1, y1, x2, y2 = map(int, block.coordinates)
    # Draw red bounding box
    rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=0.5, edgecolor='red', facecolor='none')
    axes[0].add_patch(rect)
    # Draw text (with a small margin)
    axes[0].text(x1 + 2, y1 + 15, block.text, fontsize=8, color='black', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

# Right: Original image for comparison
axes[1].imshow(image_rgb)
axes[1].set_title("Original Image")
axes[1].axis('off')

plt.tight_layout()
plt.show()


## Filter the returned text blocks


filtered_residence = layout.filter_by(
    lp.Rectangle(x_1=132, y_1=300, x_2=264, y_2=840)
)
lp.draw_text(image, filtered_residence, font_size=16)

filter_lotno = layout.filter_by(
    lp.Rectangle(x_1=810, y_1=300, x_2=910, y_2=840),
    soft_margin = {"left":10, "right":20} # Without it, the last 4 rows could not be included
)
lp.draw_text(image, filter_lotno, font_size=16)


## Group Rows based on hard-coded parameteres

y_0 = 307
n_rows = 13
height = 41
y_1 = y_0+n_rows*height

row = []
for y in range(y_0, y_1, height):
    
    interval = lp.Interval(y,y+height, axis='y')
    residence_row = filtered_residence.\
        filter_by(interval).\
        get_texts()

    lotno_row = filter_lotno.\
        filter_by(interval).\
        get_texts()
    
    row.append([''.join(residence_row), ''.join(lotno_row)])

print(row)

## An Alternative Method - Adaptive Grouping lines based on distances

blocks = filter_lotno

blocks = sorted(blocks, key = lambda x: x.coordinates[1])
    # Sort the blocks vertically from top to bottom 
distances = np.array([b2.coordinates[1] - b1.coordinates[3] for (b1, b2) in zip(blocks, blocks[1:])])
    # Calculate the distances: 
    # y coord for the upper edge of the bottom block - 
    #   y coord for the bottom edge of the upper block
    # And convert to np array for easier post processing
plt.hist(distances, bins=50);
plt.axvline(x=3, color='r');
    # Let's have some visualization 
distance_th = 0

distances = np.append([0], distances) # Append a placeholder for the first word
block_group = (distances>distance_th).cumsum() # Create a block_group based on the distance threshold 

print(block_group)
'''
# Group the blocks by the block_group mask 
grouped_blocks = [[] for i in range(max(block_group)+1)]
for i, block in zip(block_group, blocks):
    grouped_blocks[i].append(block) 

def group_blocks_by_distance(blocks, distance_th):

    blocks = sorted(blocks, key = lambda x: x.coordinates[1])
    distances = np.array([b2.coordinates[1] - b1.coordinates[3] for (b1, b2) in zip(blocks, blocks[1:])])

    distances = np.append([0], distances)
    block_group = (distances>distance_th).cumsum()

    grouped_blocks = [lp.Layout([]) for i in range(max(block_group)+1)]
    for i, block in zip(block_group, blocks):
        grouped_blocks[i].append(block) 
        
    return grouped_blocks
A = group_blocks_by_distance(filtered_residence, 5)
B = group_blocks_by_distance(filter_lotno, 10) 

# And finally we combine the outputs 
height_th = 30
idxA, idxB = 0, 0

result = []
while idxA < len(A) and idxB < len(B):
    ay = A[idxA][0].coordinates[1]
    by = B[idxB][0].coordinates[1]
    ares, bres = ''.join(A[idxA].get_texts()), ''.join(B[idxB].get_texts())
    if abs(ay - by) < height_th:
        idxA += 1; idxB += 1
    elif ay < by:
        idxA += 1; bres = ''
    else: 
        idxB += 1; ares = ''
    result.append([ares, bres])
    
print(result)

# Save the results as a table
df = pd.DataFrame(row, columns=['residence', 'lot no'])
print(df)
df.to_csv("table_layoutparser.csv", index=None)
'''




