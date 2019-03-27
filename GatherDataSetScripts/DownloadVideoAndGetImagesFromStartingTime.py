import youtube_dl
import GatherDataSetScripts.Video as VideoClass
import logging
import os
import json
import tempfile
import shutil


def dump_file(data_set_location, videos):
    with open(data_set_location, 'w+') as videos_file:
        # Clear the json file and dump
        videos_file.truncate(0)
        json.dump([video.__dict__ for video in videos], videos_file)


def handle_video_download_and_conversion_to_images(data_set_location, data_videos_set_location,
                                                   data_images_set_location_intro,
                                                   data_images_set_location_card_select,
                                                   data_images_set_location_draft,
                                                   data_images_set_location_game_start,
                                                   data_images_set_location_other):
    youtube_videos_urls = "http://www.youtube.com/watch?v="
    frames_per_second = 0.5
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': data_videos_set_location + '\\%(id)s.%(ext)s'
    }

    with open(data_set_location, 'r') as videos_file:
        videos = VideoClass.convert_json_to_object(videos_file)

        for video in videos:

            if video.is_video_downloaded:
                continue

            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    # Download video
                    ydl.download([youtube_videos_urls + video.video_id])

                input_file_location = f"{data_videos_set_location}\\{video.video_id}.mp4"

                with tempfile.TemporaryDirectory() as tmp_dir:
                    convert_video_to_images(input_file_location, tmp_dir, frames_per_second)
                    place_images_in_the_right_folders(video.video_id,
                                                      tmp_dir,
                                                      frames_per_second,
                                                      video.game_starting_time,
                                                      data_images_set_location_intro,
                                                      data_images_set_location_card_select,
                                                      data_images_set_location_draft,
                                                      data_images_set_location_game_start,
                                                      data_images_set_location_other)

                video.is_video_downloaded = True
            except Exception as error:
                logging.error(error)

    # dump_file(data_set_location, videos)


def convert_video_to_images(input_file_location, output_folder, frames_per_second):
    os.system(f"ffmpeg -i \"{input_file_location}\" -vf fps={frames_per_second} \"{output_folder}\\%05d.jpg\"")


def place_images_in_the_right_folders(video_id, images_locations, frames_per_second,
                                      game_starting_time,
                                      data_images_set_location_intro,
                                      data_images_set_location_card_select,
                                      data_images_set_location_draft,
                                      data_images_set_location_game_start,
                                      data_images_set_location_other):
    # This is an approx
    seconds_after_starting_comments = 20
    game_starting_time_in_seconds = [convert_from_time_to_second(time) for time in game_starting_time]

    for filename in os.listdir(images_locations):
        timestamp_in_seconds = (int(filename.split('.')[0]) - 1) * (1 / frames_per_second)
        full_file_path = f"{images_locations}\\{filename}"

        # Indicates this does not contains game play
        if len(game_starting_time_in_seconds) == 0:
            move_file(full_file_path, data_images_set_location_other, video_id, filename)
        elif len(game_starting_time_in_seconds) == 1:
            # This indicates normal game with card select
            starting_time = game_starting_time_in_seconds[0]

            if timestamp_in_seconds < starting_time:
                move_file(full_file_path, data_images_set_location_intro, video_id, filename)
            elif timestamp_in_seconds >= starting_time and (starting_time + seconds_after_starting_comments) < timestamp_in_seconds:
                move_file(full_file_path, data_images_set_location_card_select, video_id, filename)
            else:
                move_file(full_file_path, data_images_set_location_game_start, video_id, filename)
        elif len(game_starting_time_in_seconds) == 2:
            # This indicates area game with Draft pick
            draft_starting_time = game_starting_time_in_seconds[0]
            card_select_starting_time = game_starting_time_in_seconds[1]

            if timestamp_in_seconds < draft_starting_time:
                move_file(full_file_path, data_images_set_location_intro, video_id, filename)
            elif draft_starting_time <= timestamp_in_seconds < card_select_starting_time:
                move_file(full_file_path, data_images_set_location_draft, video_id, filename)
            elif timestamp_in_seconds >= card_select_starting_time and \
                    (card_select_starting_time + seconds_after_starting_comments) < timestamp_in_seconds:
                move_file(full_file_path, data_images_set_location_card_select, video_id, filename)
            else:
                move_file(full_file_path, data_images_set_location_game_start, video_id, filename)
            return
        else:
            # This is an error
            return


def convert_from_time_to_second(game_starting_time):
    split_string = game_starting_time.split(':')

    return int(split_string[0]) * 60 + int(split_string[1])


def move_file(current_location, new_location, video_id, file_name):
    shutil.move(current_location, f"{new_location}\\{video_id}_{file_name}")
