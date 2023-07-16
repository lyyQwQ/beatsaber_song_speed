import os
import json

from pydub.utils import mediainfo


# @brief: 获取音频文件的时长
# @param audio_path: 音频文件路径
# @return: 音频文件的时长
def get_audio_duration(audio_path):
    audio_info = mediainfo(audio_path)
    duration = float(audio_info["duration"])
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
    print(total_blocks)
    return total_blocks


def move_song_to_folder(song_path, speed):
    # 根据速度决定要移动到哪个文件夹
    speed_category = min(int(speed), 10)
    speed_folder_name = str(speed_category)
    if speed_category >= 10:
        speed_folder_name = "10+"
    target_folder = os.path.join(os.path.dirname(song_path), speed_folder_name)
    # 如果目标文件夹不存在，创建它
    if not os.path.exists(target_folder):
        os.mkdir(target_folder)
    # 移动歌曲文件
    target_path = os.path.join(target_folder, os.path.basename(song_path))
    # os.rename(song_path, target_path)
    # 如果文件已经存在，则不移动
    if not os.path.exists(target_path):
        os.rename(song_path, target_path)


# @brief: 获取所有谱面的方块数和时间
# @param base_dir: 谱面文件夹路径，会遍历所有子文件夹
def classify_songs(base_dir):
    song_dict = {}
    # 遍历所有info文件
    for song_folder in os.listdir(base_dir):
        info_path = os.path.join(base_dir, song_folder, "info.dat")
        if not os.path.exists(info_path):
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
        beatmap_paths = [os.path.join(os.path.dirname(info_path), f) for f in os.listdir(os.path.dirname(info_path)) if f.endswith('.dat')]
        print(beatmap_paths)
        # 去除info文件路径
        beatmap_paths = [path for path in beatmap_paths if path != info_path]
        max_blocks = 0
        for beatmap_path in beatmap_paths:
            total_blocks = get_block_and_time(beatmap_path, bpm)
            if type(total_blocks) is tuple:
                total_blocks = total_blocks[0]
            if total_blocks > max_blocks:
                max_blocks = total_blocks

        print("方块数：", max_blocks)
        speed = max_blocks / audio_duration
        print("速度：", speed)
        song_dict[(song_name, song_author)] = speed
        # 移动歌曲文件
        move_song_to_folder(song_folder, speed)
    return song_dict


if __name__ == '__main__':
    base_dir = "song"
    song_dict = classify_songs(base_dir)
    print(song_dict)
    # 遍历输出
    for song_name, song_author in song_dict:
        print(song_name, song_author, song_dict[(song_name, song_author)])
