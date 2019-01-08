import os
import re


# Writes a text file of all images in a directory for import into TrakEM2.
#
#
# 1) Change the image directory path and the name of the output coordinate file.
# 2) Update `regex_to_match` to match the image file names.
#    {grid} and {section} will match any number and indicate a new section on change.
#
# 3) Update any additional parameters that might have changed from last time.
#
# If `advanced` is set to false, then all images in the folder will simply be
# added on seperate sections.



###############################################################################


image_directory = r'/mnt/ssd1/sem_ad/W04/'
name_of_coordfile = 'w04_coords.txt'


###############################################################################

z_start = 0
advanced = True

# Advanced options ############################################################

#regex_to_match = 'w{grid}_tiles_combined' + os.sep + 'Section_{section}_r[0-9]+_c[0-9]+.png' 
regex_to_match = 'Section_{section}_r[0-9]+_c[0-9]+.tif'


images_per_row = 1
image_width = 8192 #3504
image_height = 8192 #2672
montage_image_overlap = 0.1 #10%

section_width = 30

skip_grids_smaller_than = 0
skip_grids_bigger_than = 1000000

coord_file_to_exclude = None #'coords.txt'


###############################################################################



def writeCoordLine(f, f_path, x, y, z):
    x_coord = x * image_width * (1 - montage_image_overlap)
    y_coord = y * image_height * (1 - montage_image_overlap)
    f.write('\t'.join(map(str, [f_path, x_coord, y_coord, z*section_width])) + '\n')


coordf_path = os.path.join(image_directory, name_of_coordfile)
coordf_path_to_exclude = os.path.join(image_directory, coord_file_to_exclude or '')

z = z_start-1

if advanced:
    
    regex = '^.+' + os.sep + regex_to_match.format(
        grid='(?P<grid>[0-9]+)',
        section='(?P<sec>[0-9]+)', 
        image='(?P<im>[0-9]+)'
    ).replace('\\', '\\\\').replace('.', '\.') + '$'

    def getSortKey(f):
        m = re.match(regex, f)
        im = -1
        if 'im' in m.groupdict():
            im = m.group('im')
            
        groups_used = m.groupdict().keys()
        if 'grid' in groups_used and 'sec' in groups_used:
            return map(int, (m.group('grid'), m.group('sec'), im))
        return map(int, (m.group('sec'), im))
    
    
    def getPathToImagesInDir(im_dir, to_exclude, im_list=[]):
            
        for f in sorted(os.listdir(im_dir)):
            
            if f in to_exclude:
                continue

            if f == name_of_coordfile:
                continue
            
            if f.startswith('trakem2.'):
                continue
            if f.startswith('unused_images'):
                continue
            
            f_path = os.path.join(im_dir, f)
            
            if os.path.isdir(f_path):
                im_list = getPathToImagesInDir(os.path.join(im_dir, f), to_exclude, im_list)
                continue
            
            if re.match(regex, f_path):
                im_list.append(f_path)
                
            elif not f.endswith(regex_to_match[-3:]):
                continue
            else:
                print 'WARNING:', f_path, 'does not match the expected format.'
            
        return im_list
    
    
    im_count = 0
    last_grid_num, last_sec_num = -1, -1
    x, y = -1, -1
    
    to_exclude = []
    if coord_file_to_exclude:
        with open(coordf_path_to_exclude) as f:
            for l in f:
                fname = l.split('\t')[0].split('/')[-1]
                to_exclude.append(fname)
            

    with open(coordf_path, 'w') as coordfile:
        
        imlist = sorted(getPathToImagesInDir(image_directory, to_exclude), key=getSortKey)
    
        for f in imlist:
        
            m = re.match(regex, f)
            groups_used = m.groupdict().keys()
            if 'grid' in groups_used and 'sec' in groups_used:
                grid_num, sec_num = map(int, (m.group('grid'), m.group('sec')))
            else:
                grid_num, sec_num = 0, int(m.group('sec'))
            

            # Skips grids specified.
            if grid_num < skip_grids_smaller_than or grid_num > skip_grids_bigger_than:
                continue
            
            # Increase x, y, and z counts as needed.
            if last_grid_num != grid_num or last_sec_num != sec_num:
                x, y = 0, 0
                z += 1
            else:
                x += 1
                if x >= images_per_row:
                    x = 0
                    y += 1
    
            last_grid_num, last_sec_num = grid_num, sec_num        
    
            # Write to output coordinate file.
            im_count += 1
            writeCoordLine(coordfile, f, x, y, z)
            
    print '::'
    print 'Wrote file', coordf_path, 'with', im_count, 'images on', z+1, 'sections.'
    print '::'
            
else:

    with open(coordf_path, 'w') as coordfile:
        
        files = [f for f in os.listdir(image_directory) if f.endswith('.tif')]
        
        for f in sorted(files, key=lambda im: int(re.findall('[0-9]+', im)[0])):
            
            if f == name_of_coordfile:
                continue
        
            # Write to output coordinate file.
            z += 1
            writeCoordLine(coordfile, os.path.join(image_directory, f), 0, 0, z)
    
    print '::'
    print 'Wrote file', coordf_path, 'with', z+1, 'images'
    print '::'

