from manim import *
from numpy import sin, cos, sign, sum
from random import random

# config.background_color = WHITE
# manim -pql -s result.py

class Result(Scene):
    caption = None
    animations_queue = []

    def construct(self):
        ## HEADINGS
        headerT = UP*3.2
        content_y = 0.5
        dbT = SVGMobject('database.svg').set_color(WHITE).scale(0.5).move_to(headerT + RIGHT*4)
        appT = Text('App').move_to(headerT + LEFT*4)
        app_gearT = SVGMobject('gear.svg').set_color(BLUE_C).scale(0.35).move_to(appT.get_center()).shift(DOWN*4.5)
        driverT = Text('Driver').move_to(headerT + LEFT*0.5)
        divider = DashedLine((2, dbT.get_y(), 0), (2, -2, 0)).set_opacity(0.5)
        clientT = Text('CLIENT').scale(0.5).align_to(config.left_side, LEFT).rotate(PI/2).shift(0.5*UP)
        serverT = Text('SERVER').scale(0.5).align_to(config.right_side, RIGHT).rotate(-PI/2).shift(0.5*UP)
        self.add(dbT, appT, driverT, divider, clientT, serverT)

        ## QUERY FROM APP TO DB
        queryT = Text('Query').move_to((appT.get_x(), content_y, 0))
        self.describe(Text('Your application crafts a Cypher query.'))
        self.play(FadeIn(queryT))
        self.wait()
        self.play(queryT.animate.move_to((driverT.get_x(), queryT.get_y(), 0)))
        query_box = SurroundingRectangle(queryT, buff=SMALL_BUFF, color=YELLOW)
        self.describe(Text('The driver sends it to the Neo4j server through the Bolt protocol.'))
        self.play(Create(query_box), run_time=0.8)
        query = VGroup(queryT, query_box)
        self.play(query.animate.move_to((dbT.get_x(), queryT.get_y(), 0)), run_time=0.8)
        self.wait(2)

        ## SERVER LOADING
        self.describe(Text('The database fetches the result.'), enqueue=False)
        loader = Dot(radius=0.05).next_to(dbT, RIGHT)
        path = Circle(0.25).flip().next_to(dbT, RIGHT)
        self.play(FadeOut(query_box))
        self.play(FadeOut(queryT, target_position=dbT.get_bottom(), scale=1), run_time=0.5)
        self.play(MoveAlongPath(loader, path), rate_func=smooth, run_time=0.8)
        self.play(MoveAlongPath(loader, path), rate_func=smooth, run_time=0.8)
        self.play(FadeOut(loader), run_time=0.5)

        ## SERVER CURSOR & RESULT LOADING
        record_size = (0.6, 0.5)
        total_records = 20
        driver_buf_size = 9
        server_buff_size = 5
        ncols = 3
        nrows = int(driver_buf_size/ncols)

        def gen_record_entry(i, opacity=None):
            '''
            Generate a record rectangle.
            '''
            recordT = Text(f'#{i}').set_z_index(i+1)  # z index for rectangle fill
            record_box = Rectangle(width=record_size[0], height=record_size[1], color=WHITE, fill_color=BLACK, fill_opacity=0.8).set_z_index(i)
            recordT.scale_to_fit_width(record_box.width-0.1)
            if i < 10: recordT.scale(0.7)  # double digits take more space than single
            record = VGroup(recordT, record_box)
            if opacity is not None:
                record.set_opacity(opacity)
            elif i >= server_buff_size:
                record.set_opacity(0)
            else:
                record.set_opacity(1/(i+1))
            return record

        server_buffer = Rectangle(height=record_size[1], width=record_size[0]*server_buff_size, stroke_color=[BLACK, WHITE, WHITE, BLACK]).shift(DOWN)
        server_buffer.move_to((dbT.get_x(), content_y, 0))
        server_cursor = Triangle(color=BLUE_C).rotate(PI).scale(0.1).align_to(server_buffer, LEFT+UP)
        server_cursor.shift((server_cursor.height+0.1) * UP).shift((server_buffer.width/4) * RIGHT)
        self.play(GrowFromPoint(server_buffer, dbT.get_center()), GrowFromPoint(server_cursor, dbT.get_center()), enqueue=True)

        driver_buf = Rectangle(width=record_size[0]*ncols, height=record_size[1]*nrows).move_to((driverT.get_x(), content_y, 0))

        # dummy record only to align the next ones
        prev_record = gen_record_entry(0)
        prev_record.align_to(server_buffer, UP).align_to(server_cursor, LEFT).shift((prev_record[1].width/2 - server_cursor.width/2) * LEFT)
        prev_record.shift(record_size[0] * LEFT)  # offset by one record so the next record will be in the right place

        '''
        Each record = a dict with entries for the record in server, driver, and app; each properly positioned.
        The flow is to only show the object for the server, and move it around (to avoid issues with ReplacementTransform) using the other objects (driver/app) for alignment.
        '''
        records = []
        for i in range(total_records):
            # record in server cursor
            record_server = gen_record_entry(i)
            record_server.align_to(prev_record, UP+RIGHT).shift(record_size[0] * RIGHT)
            prev_record = record_server

            # record in driver buffer
            record_driver = gen_record_entry(i, opacity=1)
            record_driver.align_to(driver_buf, UP+LEFT)
            pos_in_buff = (record_driver.get_center() +
                           RIGHT*(i % driver_buf_size % ncols) * record_size[0] +  # col placement
                           DOWN*(i % driver_buf_size // ncols) * record_size[1])   # row placement
            record_driver.move_to(pos_in_buff)

            # record in app
            record_app = gen_record_entry(i, opacity=1)
            record_app.move_to((appT.get_x(), content_y, 0) + self.rand_displacement(0.3))

            records.append({'server': record_server, 'driver': record_driver, 'app': record_app})

        create_server_records = AnimationGroup(*[GrowFromPoint(r['server'], dbT.get_center()) for r in records])
        self.play(create_server_records)
        self.wait()

        def move_records_from_server_to_driver(moving_range):
            '''
            Prepares a list of animations for moving records from `records` in
            the given range from server cursor to driver buffer.
            '''
            records_anims = []
            for i in moving_range:
                anim_buffer = [records[i]['server'].animate.move_to(records[i]['driver'].get_center()).set_opacity(1)]
                for j in range(i+1, total_records):
                    if j-i <= server_buff_size:
                        anim_buffer.append(records[j]['server'].animate.shift(record_size[0]*(i % driver_buf_size + 1) * LEFT).set_opacity(1/(j-i)))
                    else:
                        anim_buffer.append(records[j]['server'].animate.shift(record_size[0]*(i % driver_buf_size + 1) * LEFT))
                records_anims.append(AnimationGroup(*anim_buffer, run_time=0.3))
            return records_anims

        # MOVE 1ST BATCH OF RECORDS FROM SERVER TO DRIVER
        t1 = Text('The server sends the first batch of results (default batch size is 1000).')
        t2 = Text('The driver stores results in a buffer until your application asks for them.',
                  t2w={'buffer': BOLD}).next_to(t1, DOWN, buff=0.3)
        t = VGroup(t1, t2)
        self.describe(t, enqueue=False)
        records_anims = move_records_from_server_to_driver(range(min(driver_buf_size, total_records)))
        self.play(FadeIn(driver_buf))
        self.play(Succession(*records_anims))
        self.wait(3)

        # NEXT AND FETCH ACTIONS ON APP - PROCESS RECORDS
        def process_record(i):
            '''Prepares animation for a record to be processed (gear movement).'''
            return AnimationGroup(
                Rotate(app_gearT, angle=PI/4),
                FadeOut(records[i]['server'], target_position=app_gearT, scale=1)
            )

        t1 = Text('Your application fetches records from the driver buffer.')
        t2 = Text('It can process records while other records are still flowing.',
                  t2w={'process records': BOLD}).next_to(t1, DOWN, buff=0.3)
        t = VGroup(t1, t2)
        self.describe(t, enqueue=False)
        self.play(FadeIn(app_gearT))

        app_action_next = Text('next').scale(0.8).next_to(appT, DOWN, buff=0.5)
        self.play(
            AnimationGroup(
                Indicate(app_action_next),
                records[0]['server'].animate.move_to(records[0]['app'].get_center())
            )
        )
        self.wait()
        self.play(process_record(0))  # can't merge with prev animation because record object would move from db space, not driver
        self.wait()

        self.play(
            AnimationGroup(
                Indicate(app_action_next),
                records[1]['server'].animate.move_to(records[1]['app'].get_center())
            )
        )
        self.play(FadeOut(app_action_next))
        self.play(process_record(1))
        self.wait()

        app_action_fetch = Text('fetch').scale(0.8).next_to(appT, DOWN, buff=0.5)
        anims = [r['server'].animate.move_to(r['app'].get_center()) for r in records[2:driver_buf_size]]
        self.play(Indicate(app_action_fetch), LaggedStart(*anims, lag_ratio=0.25))
        self.play(LaggedStart(process_record(2), FadeOut(app_action_fetch), lag_ratio=0.25))
        self.wait(3)

        records_anims = move_records_from_server_to_driver(range(
            driver_buf_size,
            min(driver_buf_size*2, total_records)
        ))

        # 2ND BATCH OF RECORDS FROM SERVER TO DRIVER
        self.describe(Text("When there are no more records in the driver buffer, the driver fetches more from the server."))
        self.play(
            LaggedStart(
                Succession(*records_anims),
                Succession(*[process_record(i) for i in range(3, 6)], lag_ratio=2)
            )
        )
        self.wait(3)

        # CONSUME & RESULT SUMMARY
        self.play(process_record(6))
        t1 = Text('If consume() is called at any point, all unconsumed results are discarded',
                  t2c={'consume()': YELLOW}, t2w={'discarded': BOLD})
        t2 = Text('and the driver receives the result summary.').next_to(t1, DOWN, buff=0.3)
        t = VGroup(t1, t2)
        self.describe(t, enqueue=False)
        app_action_consume = Text('consume()').scale(0.8).next_to(appT, DOWN, buff=0.5)
        to_discard = VGroup(*[r['server'] for r in records[driver_buf_size:]])  # we know we've only fetched up to the 1st batch
        self.play(Indicate(app_action_consume))
        self.play(FadeOut(to_discard), FadeOut(server_cursor), FadeOut(server_buffer), FadeOut(driver_buf), run_time=1.5)

        summaryT = Text('Summary').scale(0.5).move_to((dbT.get_x(), content_y, 0))
        summary_box = SurroundingRectangle(summaryT, buff=SMALL_BUFF, color=YELLOW)
        summary = VGroup(summaryT, summary_box)
        self.play(GrowFromPoint(summaryT, dbT))
        self.play(Create(summary_box))
        self.play(summary.animate.move_to((driverT.get_x(), queryT.get_y(), 0)), run_time=0.8)
        self.play(FadeOut(summary_box))
        self.play(FadeOut(app_action_consume))
        self.wait()

        # FINISH PROCESSING
        t1 = Text('Records fetched by the application are still available.')
        t2 = Text('Unconsumed records are no longer accessible.').next_to(t1, DOWN, buff=0.3)
        t = VGroup(t1, t2)
        self.describe(t)
        self.play(Succession(*[process_record(i) for i in range(7, driver_buf_size)], lag_ratio=1.5))

        self.wait(5)

    def describe(self, text, enqueue=True):
        '''
        Display/Update bottom caption.
        '''
        caption_pos = DOWN*2.9
        text.move_to(caption_pos)
        text.scale(0.4)
        if self.caption == None:
            self.play(Write(text), run_time=0.4, enqueue=enqueue)
        else:
            self.play(ReplacementTransform(self.caption, text), enqueue=enqueue)
        self.caption = text  # ReplacementTransform needs a reference to the previous object!

    def rand_displacement(self, factor=0.5):
        return sign(random()-factor)*LEFT*random() + sign(random()-factor)*UP*random()

    def play(self, *args, enqueue=False, subcaption=None, subcaption_duration=None, subcaption_offset=0, **kwargs):
        '''
        A wrapper for Manim's `play`, to be able to enqueue a bunch of animations
        and wait until buffer is flushed for them to play all together.
        '''
        self.animations_queue += args

        if not enqueue:
            super().play(*self.animations_queue, subcaption=subcaption, subcaption_duration=subcaption_duration, subcaption_offset=subcaption_offset, **kwargs)
            self.animations_queue = []