import sys
import logging

from vispy import scene
from vispy.scene.visuals import Text
from vispy import app
import numpy as np

import pandas as pd

from imageio import imread

import click

from skimage.draw import circle

canvas = scene.SceneCanvas(keys='interactive')
canvas.size = 800, 600
canvas.show()

# Set up a viewbox to display the image with interactive pan/zoom
view = canvas.central_widget.add_view()


@click.command()
@click.argument('image_fpath')
@click.argument('output_fpath')
def main(image_fpath, output_fpath):
    global canvas

    logging.basicConfig(level=logging.INFO)

    im = imread(image_fpath)
    logging.info(f"Loaded image with shape {im.shape}")
    image = scene.visuals.Image(im, parent=view.scene)


    app.current_pos = None

    try:
        df = pd.read_csv(output_fpath)
        points = [(p.X, p.Y) for p in df.itertuples()]
    except FileNotFoundError:
        points = []

    @canvas.events.mouse_press.connect
    def on_mouse_press(event):
        # print("Press pos:", event.pos)
        # get transform mapping from canvas to image
        tr = view.node_transform(image)
        # print("Image pos:", tr.map(event.pos)[:2])
        x, y = tr.map(event.pos)[:2]

        print("Click at ", x, y)

        # c, r = int(x), int(y)

        # points.append(np.array((r, c)))

        # rr, cc = circle(r, c, 5)
        # im[rr, cc] = 255, 0, 0
        # image.set_data(im)
        # canvas.update()

    @canvas.connect
    def on_mouse_move(event):
        app.current_pos = event.pos

    def update_drawing():
        draw_im = im.copy()
        for r, c in points:
            rr, cc = circle(r, c, 5)
            draw_im[rr, cc] = 255 #, 0, 0
        image.set_data(draw_im)
        canvas.update()

    @canvas.events.key_press.connect
    def key_event(event):
        if event.key.name == 'P':
            print("Added point")
            tr = view.node_transform(image)
            x, y = tr.map(app.current_pos)[:2]
            c, r = int(x), int(y)
            points.append(np.array((r, c)))
            update_drawing()

        if event.key.name == 'D':
            tr = view.node_transform(image)
            x, y = tr.map(app.current_pos)[:2]
            c, r = int(x), int(y)
            deltas = np.array(points) - np.array((r, c))
            sq_dists = np.sum(deltas * deltas, axis=1)
            del points[np.argmin(sq_dists)]
            update_drawing()

        if event.key.name == 'S':
            df = pd.DataFrame(points, columns=['X', 'Y'])
            df.to_csv(output_fpath, index=False)

    t1 = scene.visuals.Text('Text in root scene (24 pt)', parent=image, color='red', pos=(100,100))
    t1.font_size = 24
    # Set 2D camera (the camera will scale to the contents in the scene)
    view.camera = scene.PanZoomCamera(aspect=1)
    view.camera.set_range()
    view.camera.flip = (False, True, False)

    update_drawing()

    app.run()


if __name__ == '__main__':
    main()
