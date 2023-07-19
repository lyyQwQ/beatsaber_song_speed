import os
import json
import shutil

# from pydub.utils import mediainfo
import mutagen


# @brief: 获取音频文件的时长
# @param audio_path: 音频文件路径
# @return: 音频文件的时长
def get_audio_duration(audio_path):
    duration = mutagen.File(audio_path).info.length
    # 前后包含静音部分，可能没有谱面，所以减去1秒
    return duration - 1


# @brief: 获取一个谱面的歌曲名、作者名和bpm
# @param info_path: info文件路径
# @return: 歌曲名、作者名和bpm
def get_song_info_and_bpm(info_path):
    with open(info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
    return info["_songName"], info["_songAuthorName"], info["_beatsPerMinute"]


# @brief: 获取一个谱面的方块数和时间
# @param beatmap_path: 谱面路径
# @param bpm: 谱面的bpm
def get_block_and_time(beatmap_path, bpm):
    with open(beatmap_path, 'r', encoding='utf-8') as f:
        beatmap = json.load(f)
    # 获取谱面版本
    version = beatmap.get("version", "2.0.0")

    # 如果不存在"_notes"或"colorNotes"，及没有任何方块，那么返回0个块，1秒
    note_key = "_notes" if version.startswith("2.") else "colorNotes"
    if note_key not in beatmap:
        return 0, 1

    # 计算方块数和时间，方块数为"_type"为0、1、2的方块数，3为地雷，4为滑条，所以只计算0、1、2
    type_key = "_type" if version.startswith("2.") else "c"
    total_blocks = len([note for note in beatmap[note_key] if note[type_key] in {0, 1, 2}])

    # 输出块数和时间，时间显示为几分几秒
    # print(total_blocks, total_time_in_seconds // 60, total_time_in_seconds % 60)
    # print(total_blocks)
    return total_blocks


# @brief: 将歌曲移动到对应的文件夹
# @param song_path: 歌曲路径
# @param speed: 歌曲速度
# @param max_songs: 每个子文件夹最多的歌曲数
def move_song_to_folder(song_path, speed, max_songs=50):
    # 根据速度决定要移动到哪个文件夹
    speed_category = min(int(speed), 12)
    speed_folder_name = str(speed_category)
    if speed_category >= 12:
        speed_folder_name = "12以上"
    # todo 移动到CustomMusic文件夹下
    # target_folder = os.path.join(os.path.dirname(song_path), "CustomMusic", speed_folder_name)
    target_folder = os.path.join(os.path.dirname(song_path), speed_folder_name)
    # Check how many songs already exist in the folder
    subfolder_counter = 1
    current_target_folder = target_folder
    while os.path.exists(current_target_folder) and len(os.listdir(current_target_folder)) >= max_songs:
        subfolder_counter += 1
        current_target_folder = f"{target_folder}-{subfolder_counter}"
    # If the target folder doesn't exist, create it
    if not os.path.exists(current_target_folder):
        os.makedirs(current_target_folder)
    # Move song file

    target_path = os.path.join(current_target_folder, os.path.basename(song_path))
    # 如果文件存在则移动到"已存在"文件夹
    if not os.path.exists(target_path):
        # print(f'song_path: {song_path}, target_path: {target_path}, 是否存在song_path: {os.path.exists(song_path)}')
        os.rename(song_path, target_path)
    else:
        existed_folder = os.path.join(os.path.dirname(song_path), "已存在")
        if not os.path.exists(existed_folder):
            os.makedirs(existed_folder)
        # 如果"已存在"文件夹中已经存在同名文件，则删除，否则移动
        if os.path.exists(os.path.join(existed_folder, os.path.basename(song_path))):
            # 删除该文件夹，不管是否为空
            shutil.rmtree(song_path)
        else:
            os.rename(song_path, os.path.join(existed_folder, os.path.basename(song_path)))


# @brief: 获取所有谱面的方块数和时间
# @param base_dir: 谱面文件夹路径，会遍历所有子文件夹
def classify_songs(base_dir):
    song_dict = {}
    # 遍历所有info文件
    for song_folder in os.listdir(base_dir):
        # print("当前歌曲文件夹路径", song_folder)
        info_path = os.path.join(base_dir, song_folder, "info.dat")
        # print(info_path)
        if not os.path.exists(info_path):
            info_path = os.path.join(base_dir, song_folder, "Info.dat")
            if not os.path.exists(info_path):
                # print("info文件不存在", info_path)
                continue
            # 获取歌曲名、作者名和bpm
        song_name, song_author, bpm = get_song_info_and_bpm(info_path)
        # 获取音频文件的路径
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        audio_path = os.path.join(os.path.dirname(info_path), info["_songFilename"])
        # 获取音频的时长
        audio_duration = get_audio_duration(audio_path)
        # print("音频时长：", audio_duration)
        beatmap_paths = [os.path.join(os.path.dirname(info_path), f) for f in os.listdir(os.path.dirname(info_path)) if
                         f.endswith('.dat')]
        # print(beatmap_paths)
        # 去除info文件路径
        beatmap_paths = [path for path in beatmap_paths if path != info_path]
        max_blocks = 0
        for beatmap_path in beatmap_paths:
            total_blocks = get_block_and_time(beatmap_path, bpm)
            # 莫名其妙的bug，我上面的函数已经只返回一个值了，但有的时候返回来的还是元组，所以这里再判断一下
            if type(total_blocks) is tuple:
                total_blocks = total_blocks[0]
            if total_blocks > max_blocks:
                max_blocks = total_blocks

        # print("方块数：", max_blocks)
        speed = max_blocks / audio_duration
        # print("速度：", speed)
        song_dict[(song_name, song_author)] = speed
        # 移动歌曲文件
        move_song_to_folder(os.path.join(base_dir, song_folder), speed)
    return song_dict


if __name__ == '__main__':
    base_dir = "song"
    song_dict = classify_songs(base_dir)
    print(song_dict)
    # 遍历输出
    for song_name, song_author in song_dict:
        print(song_name, song_author, song_dict[(song_name, song_author)])
