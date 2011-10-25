from scipy.io import loadmat
import numpy as np
import os
from glob import glob

from img_funcs import draw_bounding_boxes, grab_bounding_boxes
import xml.etree.ElementTree as ET
#import elementtree.ElementTree as ET

from IPython.core.debugger import Tracer
tracer = Tracer()

class ImageNetData(object):
    """ ImageNetData needs path to meta.mat, path to images and path to annotations.
     The images are assumed to be in folders according to their synsets names """
    def __init__(self, meta_path, image_path, annotation_path):
        self.image_path = image_path
        self.annotation_path = annotation_path
        self.meta_data = loadmat(meta_path)
        self.synsets = np.squeeze(self.meta_data['synsets'])
        self.ids = np.squeeze(np.array([x[0] for x in self.synsets]))
        self.wnids = np.squeeze(np.array([x[1] for x in self.synsets]))
        self.word = np.squeeze(np.array([x[2] for x in self.synsets]))
        self.num_children = np.squeeze(np.array([x[4] for x in self.synsets]))
        self.children = [np.squeeze(x[5]).astype(np.int) for x in self.synsets]

    def get_class(self, search_string):
        indices = np.where([search_string in x[2][0] for x in self.synsets])[0]
        for i in indices:
            print(self.synsets[i])
        return indices

    def get_children(self, aclass):
        # minus one converts ids into indices in our arrays
        children = self.synsets[aclass][5][0] - 1

        print(self.synsets[aclass])
        rchildren = children.tolist()

        print "-----------------"
        for child in children:
            print self.synsets[child]
            # recurse
            if self.synsets[child][4] != 0:
                rchildren.extend(self.get_children(child))
        return rchildren

    def get_bndbox(self, classid, imageid):
        wnid = self.wnids[classid]
        annotation_file = os.path.join(self.annotation_path, str(wnid), str(wnid) + "_" + str(imageid) + ".xml")
        xmltree = ET.parse(annotation_file)
        objects = xmltree.findall("object")
        result = []
        for object_iter in objects:
            bndbox = object_iter.find("bndbox")
            result.append([int(it.text) for it in bndbox])
        #[xmin, ymin, xmax, ymax] = [it.text for it in bndbox]
        return result

    def get_image_ids(self, theclass):
        wnid = self.wnids[theclass]
        files = glob(os.path.join(self.image_path,wnid,wnid+"*"))
        filenames = [os.path.basename(f)[:-5] for f in files]
        numbers = map(lambda f: f.split("_")[1], filenames)
        return numbers

    def bounding_box_images(self, classidx):
        if not os.path.exists("output/bounding_box"):
            os.mkdir("output/bounding_box")
        #class_string = self.word[classidx]
        wnid = self.wnids[classidx]
        if not os.path.exists(os.path.join("output/bounding_box", wnid)):
            os.mkdir(os.path.join("output/bounding_box", wnid))

        image_files = self.get_image_ids(classidx)
        bbfiles = []
        for f in image_files:
            try:
                bounding_boxes = self.get_bndbox(classidx, f)
            except IOError:
                #no bounding box
                #print("no xml found")
                continue
            bbfiles.append(f)
            img_path = os.path.join(self.image_path, wnid, wnid+'_'+f+".JPEG")
            out_path = str(os.path.join("output/bounding_box", wnid, wnid+'_'+f+".png"))
            draw_bounding_boxes(img_path, bounding_boxes, out_path)
            #if len(bbfiles)>2:
                #break
        print("annotated files: %d"%len(bbfiles))

    def class_idx_from_wnid(self, wnid):
        return np.where(self.wnids==wnid)[0][0]

    def all_bounding_boxes(self, classidx):
        image_files = self.get_image_ids(classidx)
        all_bbs = []
        for f in image_files:
            img_bbs = self.get_bndbox(classidx, f)

            all_bbs.extend(grab_bounding_boxes(f, img_bbs))
            tracer()



def main():
    # ImageNetData needs path to meta.mat, path to images and path to annotations.
    # The images are assumed to be in folders according to their synsets names
    imnet = ImageNetData("ILSVRC2011_devkit-2.0/data/meta.mat", "unpacked", "annotation")
    classes = imnet.get_class("ambulance")
    aclass = classes[0]
    #aclass = imnet.class_idx_from_wnid("n01440764")
    #print imnet.synsets[aclass]
    #imnet.bounding_box_images(aclass)
    imnet.all_bounding_boxes(aclass)

    #rchildren = imnet.get_children(aclass)
    #for theclass in rchildren:
        #imnet.bounding_box_images(theclass)
    tracer()

if __name__ == "__main__":
    main()
