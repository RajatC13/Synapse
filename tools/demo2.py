import _init_paths
from fast_rcnn.config import cfg, cfg_from_file
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse
import random
import customToolbox

NETS = {'vgg16': ('VGG16',
                  'vgg_cnn_m_1024_faster_rcnn_iter_253000.caffemodel'),
        'zf': ('ZF',
                  'ZF_faster_rcnn_final.caffemodel')
        }


def vis_detections(im, class_name, ax, dets, thresh=0.5):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        return


    ax.imshow(im, aspect='equal')
    for i in inds:
        bbox = dets[i, :4]
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
            )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('Threshold = {:.1f}').format(thresh),
                 fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.draw()



def demo(net, image_name):
    """Detect object classes in an image using pre-computed object proposals."""

    # Load the demo image
    im_file = image_name
    im = cv2.imread(im_file)

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.7
    NMS_THRESH = 0.3
    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
	
        vis_detections(im, cls, ax, dets, thresh=CONF_THRESH)
    plt.savefig(str(random.randint(1,1000))+'.jpg')


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        choices=NETS.keys(), default='vgg16')
    parser.add_argument('--config', dest='cfg_path', help='config file to use for demo',
                        default='../experiments/cfgs/faster_rcnn_end2end.yml')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    # Load config file
    cfg_from_file(args.cfg_path)

    # Load category IDs from the config file
    category_ids = cfg.TRAIN.CAT_IDS

    # list up all classes that you want the demo run on. Do not forget to include __background__ as additional class.
    # If you do not know the correct string of your categories, check data/MSCOCO_API_categories.py or better
    # use create_class_tuple() from tools/customToolbox.py
    # CLASSES = ('__background__', 'person', 'car', 'dog', 'horse')

    CLASSES = customToolbox.create_class_tuple(category_ids)
    print "Classes: " + str(CLASSES)

    # The prototxt with the test net
    prototxt = os.path.join(cfg.ROOT_DIR, 'models/coco/VGG_CNN_M_1024/faster_rcnn_end2end/test.prototxt')
    print "prototxt " + prototxt

    caffemodel = os.path.join(cfg.DATA_DIR, 'faster_rcnn_models', NETS[args.demo_net][1])
    print "caffemodel " + caffemodel

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\n\nLoaded network {:s}'.format(caffemodel)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    # image names for the images on which the demo should run on.
    imgname = raw_input('Enter file name:\n')
    im_names = []
    im_names.append('/home/ayushjaiswal199/'+str(imgname))
    print(im_names)
    for im_name in im_names:
        print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print 'Demo for data/demo/{}'.format(im_name)
        demo(net, im_name)

    plt.show()