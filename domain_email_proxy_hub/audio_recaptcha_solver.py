#!/usr/bin/env python3
"""
Audio reCAPTCHA v2 Solver using SpeechRecognition + pydub + patchright
Headlessly solves invisible / checkbox reCAPTCHA v2 challenges via audio transcription.
"""

import os
import io
import time
import asyncio
import urllib.request
import speech_recognition as sr
from pydub import AudioSegment

async def solve_recaptcha_audio(page, max_retries=3):
    """
    Attempts to solve reCAPTCHA v2 challenge via the audio challenge button in bframe.
    Returns True if solved, False otherwise.
    """
    recognizer = sr.Recognizer()

    for attempt in range(max_retries):
        print(f"  [Solver] Attempt {attempt+1}/{max_retries} to solve reCAPTCHA audio challenge...")
        
        # Locate the bframe
        bframe = None
        for frame in page.frames:
            if "recaptcha" in frame.url and "bframe" in frame.url:
                bframe = frame
                break
        
        if not bframe:
            print("  [Solver] No reCAPTCHA bframe found on page.")
            return False

        # Look for audio button
        try:
            audio_btn = await bframe.wait_for_selector("#recaptcha-audio-button", timeout=5000)
            if audio_btn:
                print("  [Solver] Clicking audio challenge button...")
                await audio_btn.click()
                await asyncio.sleep(2)
        except Exception as e:
            print(f"  [Solver] Could not click audio button: {e}")

        # Check for IP block on audio challenge ("Your computer or network may be sending automated queries...")
        try:
            dos_msg = await bframe.query_selector(".rc-doscaptcha-header")
            if dos_msg:
                t = await dos_msg.inner_text()
                print(f"  [Solver] Audio challenge blocked by Google: {t}")
                return False
        except Exception:
            pass

        # Locate audio download link or audio source
        audio_url = None
        try:
            link_el = await bframe.wait_for_selector(".rc-audiochallenge-tdownload-link", timeout=7000)
            if link_el:
                audio_url = await link_el.get_attribute("href")
        except Exception:
            try:
                src_el = await bframe.wait_for_selector("#audio-source", timeout=5000)
                if src_el:
                    audio_url = await src_el.get_attribute("src")
            except Exception as e:
                print(f"  [Solver] Could not find audio source element: {e}")

        if not audio_url:
            print("  [Solver] Audio URL not found in challenge.")
            continue

        print(f"  [Solver] Downloading audio challenge: {audio_url[:60]}...")
        req = urllib.request.Request(
            audio_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        mp3_data = urllib.request.urlopen(req, timeout=10).read()

        # Convert MP3 to WAV using pydub
        sound = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        wav_buf = io.BytesIO()
        sound.export(wav_buf, format="wav")
        wav_buf.seek(0)

        with sr.AudioFile(wav_buf) as source:
            audio_recorded = recognizer.record(source)
            try:
                transcript = recognizer.recognize_google(audio_recorded)
                print(f"  [Solver] Transcribed audio: '{transcript}'")
            except sr.UnknownValueError:
                print("  [Solver] Google Speech Recognition could not understand audio.")
                # Reload challenge
                reload_btn = await bframe.query_selector("#recaptcha-reload-button")
                if reload_btn:
                    await reload_btn.click()
                    await asyncio.sleep(2)
                continue
            except sr.RequestError as e:
                print(f"  [Solver] Google Speech API request error: {e}")
                return False

        # Input the transcript into response field
        input_field = await bframe.wait_for_selector("#audio-response", timeout=5000)
        await input_field.fill(transcript)
        await asyncio.sleep(1)

        verify_btn = await bframe.wait_for_selector("#recaptcha-verify-button", timeout=5000)
        await verify_btn.click()
        await asyncio.sleep(3)

        # Check if solved
        bframe_still_visible = False
        for frame in page.frames:
            if "recaptcha" in frame.url and "bframe" in frame.url:
                try:
                    is_hidden = await frame.is_hidden("body")
                    if not is_hidden:
                        bframe_still_visible = True
                except Exception:
                    pass

        if not bframe_still_visible:
            print("  [Solver] 🎉 reCAPTCHA challenge successfully solved!")
            return True
        else:
            print("  [Solver] Challenge frame still visible, may need retry.")

    return False
