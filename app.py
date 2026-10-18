from flask import Flask, render_template_string, request, jsonify
import requests
import os
import re
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import json
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='static')

HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>اسأل صوت الحق - بوت الأخبار الذكي</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Browser Reset & Normalization */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        html {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
            text-size-adjust: 100%;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            height: 100vh;
            height: -webkit-fill-available;
            transition: background 0.3s ease;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            position: fixed;
            width: 100%;
        }

        body.light-mode {
            background: #F4F4F5;
        }

        body.dark-mode {
            background: #27272A;
        }

        .chat-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            height: -webkit-fill-available;
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 16px 20px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 16px;
            transition: all 0.3s ease;
            background: #B90000;
            border: 1px solid #A00000;
        }

        .light-mode .header {
            background: #B90000;
            border: 1px solid #A00000;
        }

        .dark-mode .header {
            background: #B90000;
            border: 1px solid #A00000;
        }

        .header-top-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 10px;
            flex-direction: row-reverse;
        }

        .header-right {
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }

        .icon-container {
            background: white;
            padding: 8px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            flex-shrink: 0;
        }

        .logo-img {
            width: 50px;
            height: 50px;
            object-fit: contain;
        }

        .title-section {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .title {
            font-size: 22px;
            font-weight: bold;
            color: white;
        }

        .subtitle {
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            color: rgba(255, 255, 255, 0.9);
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
            box-shadow: 0 0 10px white;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.9); }
        }

        .theme-toggle {
            padding: 8px;
            border-radius: 10px;
            font-size: 18px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            min-width: 40px;
            min-height: 40px;
        }

        .theme-toggle:hover {
            transform: rotate(180deg) scale(1.1);
            background: rgba(255, 255, 255, 0.3);
        }

        .back-button {
            padding: 7px 12px;
            border-radius: 10px;
            font-size: 12px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            flex-shrink: 0;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            font-weight: 600;
            text-decoration: none;
        }

        .back-button:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.3);
        }
        .header-left-buttons {
            display: flex;
            flex-direction: column;
            gap: 8px;
            align-items: flex-start;
        }

        .description-line1 {
            font-size: 12px;
            line-height: 1.4;
            color: rgba(255, 255, 255, 0.95);
            font-weight: 500;
            text-align: center;
            margin-bottom: 6px;
        }

        .description-line2 {
            font-size: 12px;
            line-height: 1.4;
            color: rgba(255, 255, 255, 0.95);
            font-weight: 500;
            text-align: center;
        }

        .messages-container {
            flex: 1;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
        }

        .light-mode .messages-container {
            background: white;
            border: 1px solid #E4E4E7;
        }

        .dark-mode .messages-container {
            background: #18181B;
            border: 1px solid #3F3F46;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        .messages::-webkit-scrollbar {
            width: 8px;
        }

        .messages::-webkit-scrollbar-track {
            background: transparent;
            border-radius: 10px;
        }

        .light-mode .messages::-webkit-scrollbar-thumb {
            background: #E4E4E7;
            border-radius: 10px;
        }

        .dark-mode .messages::-webkit-scrollbar-thumb {
            background: #3F3F46;
            border-radius: 10px;
        }

        .message {
            margin-bottom: 16px;
            display: flex;
            gap: 12px;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .message-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            overflow: hidden;
        }

        .light-mode .message.user .message-icon {
            background: #18181B;
            color: white;
            order: 1;
        }

        .dark-mode .message.user .message-icon {
            background: #FCFCFC;
            color: #18181B;
            order: 1;
        }

        .light-mode .message.assistant .message-icon {
            background: white;
            color: #18181B;
            padding: 4px;
        }

        .dark-mode .message.assistant .message-icon {
            background: white;
            color: #FCFCFC;
            padding: 4px;
        }

        .message-content {
            max-width: 70%;
            padding: 16px 20px;
            border-radius: 16px;
            line-height: 1.8;
            font-size: 15px;
            position: relative;
            transition: all 0.3s ease;
        }

        .light-mode .message.user .message-content {
            background: #B90000;
            color: white;
            border-bottom-left-radius: 4px;
        }

        .dark-mode .message.user .message-content {
            background: #B90000;
            color: white;
            border-bottom-left-radius: 4px;
        }

        .light-mode .message.assistant .message-content {
            background: #F4F4F5;
            color: #18181B;
            border-bottom-right-radius: 4px;
            border: 1px solid #E4E4E7;
        }

        .dark-mode .message.assistant .message-content {
            background: #27272A;
            color: #FCFCFC;
            border-bottom-right-radius: 4px;
            border: 1px solid #3F3F46;
        }

        .search-info {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }

        .light-mode .search-info {
            background: #E4E4E7;
            color: #18181B;
            border: 1px solid #D4D4D8;
        }

        .dark-mode .search-info {
            background: #3F3F46;
            color: #A1A1AA;
            border: 1px solid #52525B;
        }

        .sources {
            margin-top: 12px;
            padding-top: 12px;
            transition: border-color 0.3s ease;
        }

        .light-mode .sources {
            border-top: 1px solid #E4E4E7;
        }

        .dark-mode .sources {
            border-top: 1px solid #3F3F46;
        }

        .source-title {
            font-size: 11px;
            margin-bottom: 6px;
            font-weight: bold;
            transition: color 0.3s ease;
        }

        .light-mode .source-title {
            color: #71717A;
        }

        .dark-mode .source-title {
            color: #A1A1AA;
        }

        .source-link {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 11px;
            margin: 4px 4px 4px 0;
            transition: all 0.3s;
        }

        .light-mode .source-link {
            background: #B90000;
            border: 1px solid #A00000;
            color: white;
        }

        .dark-mode .source-link {
            background: #B90000;
            border: 1px solid #A00000;
            color: white;
        }

        .source-link:hover {
            transform: translateY(-2px);
        }

        .light-mode .source-link:hover {
            background: #A00000;
            border-color: #900000;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.3);
        }

        .dark-mode .source-link:hover {
            background: #A00000;
            border-color: #900000;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.3);
        }

        .input-container {
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: all 0.3s ease;
        }

        .light-mode .input-container {
            border-top: 1px solid #E4E4E7;
            background: #FCFCFC;
        }

        .dark-mode .input-container {
            border-top: 1px solid #3F3F46;
            background: #18181B;
        }

        .buttons-row {
            display: flex;
            gap: 12px;
            align-items: center;
            width: 100%;
        }

        .input-wrapper {
            position: relative;
            width: 100%;
        }

        .voice-button {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: white;
            border: 2px solid #B90000;
            font-size: 20px;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(185, 0, 0, 0.2);
        }

        .light-mode .voice-button {
            color: #B90000;
            background: white;
            border: 2px solid #B90000;
        }

        .dark-mode .voice-button {
            color: #B90000;
            background: white;
            border: 2px solid #B90000;
        }

        .voice-button:hover {
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 4px 12px rgba(185, 0, 0, 0.3);
        }

        .light-mode .voice-button:hover {
            background: #B90000;
            color: white;
            border-color: #B90000;
        }

        .dark-mode .voice-button:hover {
            background: #B90000;
            color: white;
            border-color: #B90000;
        }

        .voice-button.recording {
            animation: pulse-mic 1.5s infinite;
        }

        .light-mode .voice-button.recording {
            color: white;
            background: #52525B;
            border-color: #52525B;
        }

        .dark-mode .voice-button.recording {
            color: white;
            background: #71717A;
            border-color: #71717A;
        }

        @keyframes pulse-mic {
            0%, 100% {
                transform: translateY(-50%) scale(1);
            }
            50% {
                transform: translateY(-50%) scale(1.2);
            }
        }

        .input-field {
            width: 100%;
            padding: 16px 50px 16px 20px;
            border-radius: 16px;
            font-size: 15px;
            outline: none;
            transition: all 0.3s;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .light-mode .input-field {
            border: 1px solid #E4E4E7;
            background: #E4E4E7;
            color: #18181B;
        }

        .dark-mode .input-field {
            border: 1px solid #3F3F46;
            background: #3F3F46;
            color: #FCFCFC;
        }

        .light-mode .input-field::placeholder {
            color: #71717A;
        }

        .dark-mode .input-field::placeholder {
            color: #A1A1AA;
        }

        .input-field:focus {
            transform: scale(1.01);
        }

        .light-mode .input-field:focus {
            border-color: #18181B;
            box-shadow: 0 0 0 3px rgba(24, 24, 27, 0.1);
        }

        .dark-mode .input-field:focus {
            border-color: #71717A;
            box-shadow: 0 0 0 3px rgba(113, 113, 122, 0.2);
        }

        .send-button, .clear-button {
            flex: 1;
            padding: 16px 28px;
            border-radius: 16px;
            border: none;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 15px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-width: 120px;
        }

        .light-mode .send-button {
            background: #B90000;
            color: white;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.4);
        }

        .dark-mode .send-button {
            background: #B90000;
            color: white;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.4);
        }

        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
        }

        .light-mode .send-button:hover:not(:disabled) {
            box-shadow: 0 6px 20px rgba(185, 0, 0, 0.5);
            background: #A00000;
        }

        .dark-mode .send-button:hover:not(:disabled) {
            box-shadow: 0 6px 20px rgba(185, 0, 0, 0.5);
            background: #A00000;
        }

        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .light-mode .clear-button {
            background: white;
            color: #B90000;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            border: 2px solid #B90000;
        }

        .dark-mode .clear-button {
            background: white;
            color: #B90000;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 2px solid #B90000;
        }

        .clear-button:hover {
            transform: translateY(-2px);
            background: #FEE;
            box-shadow: 0 6px 20px rgba(185, 0, 0, 0.3);
        }

        .loading {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 16px;
            margin-bottom: 16px;
            animation: slideIn 0.3s ease-out;
            transition: all 0.3s ease;
        }

        .light-mode .loading {
            background: #F4F4F5;
            border: 1px solid #E4E4E7;
        }

        .dark-mode .loading {
            background: #27272A;
            border: 1px solid #3F3F46;
        }

        .loading.show {
            display: flex;
        }

        .loading-text {
            font-size: 14px;
            transition: color 0.3s ease;
        }

        .light-mode .loading-text {
            color: #71717A;
        }

        .dark-mode .loading-text {
            color: #A1A1AA;
        }

        .loading-dots {
            display: flex;
            gap: 6px;
        }

        .loading-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }

        .light-mode .loading-dot {
            background: #18181B;
        }

        .dark-mode .loading-dot {
            background: #FCFCFC;
        }

        .loading-dot:nth-child(1) {
            animation-delay: -0.32s;
        }

        .loading-dot:nth-child(2) {
            animation-delay: -0.16s;
        }

        @keyframes bounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1.2);
                opacity: 1;
            }
        }

        .welcome-message {
            text-align: center;
            padding: 20px 20px 40px 20px;
            transition: color 0.3s ease;
        }

        .welcome-title {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 8px;
            transition: color 0.3s ease;
        }

        .light-mode .welcome-title {
            color: #18181B;
        }

        .dark-mode .welcome-title {
            color: #FCFCFC;
        }

        .welcome-text {
            font-size: 16px;
            line-height: 1.8;
            transition: color 0.3s ease;
        }

        .light-mode .welcome-text {
            color: #71717A;
        }

        .dark-mode .welcome-text {
            color: #A1A1AA;
        }

        .quick-questions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
            margin-top: 24px;
            padding: 0 20px;
        }

        .quick-question {
            padding: 16px 20px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            font-size: 14px;
        }

        .light-mode .quick-question {
            background: white;
            border: 2px solid #B90000;
            color: #B90000;
            font-weight: 600;
        }

        .dark-mode .quick-question {
            background: #18181B;
            border: 2px solid #B90000;
            color: white;
            font-weight: 600;
        }

        .quick-question:hover {
            transform: translateY(-2px);
        }

        .light-mode .quick-question:hover {
            background: #B90000;
            color: white;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.3);
        }

        .dark-mode .quick-question:hover {
            background: #B90000;
            color: white;
            box-shadow: 0 4px 15px rgba(185, 0, 0, 0.3);
        }

        /* Desktop Compact Mode - تصغير بسيط */
        @media (min-width: 769px) {
            .chat-container {
                max-width: 1000px;
                padding: 12px;
            }
            
            .header {
                margin-bottom: 10px;
                padding: 12px 16px;
            }
            
            .header-top-row {
                margin-bottom: 6px;
            }
            
            .logo-img {
                width: 42px;
                height: 42px;
            }
            
            .title {
                font-size: 18px;
            }
            
            .subtitle {
                font-size: 11px;
            }
            
            .description-line1,
            .description-line2 {
                font-size: 11px;
                line-height: 1.3;
                margin-bottom: 3px;
            }
            
            .messages {
                padding: 16px;
            }
            
            .message {
                margin-bottom: 10px;
            }
            
            .message-content {
                padding: 12px 16px;
                font-size: 14px;
                line-height: 1.6;
            }
            
            .quick-questions {
                gap: 10px;
                margin-top: 12px;
                padding: 0 16px;
                grid-template-columns: repeat(2, 1fr);
            }
            
            .quick-question {
                padding: 12px 16px;
                font-size: 14px;
            }
            
            .input-container {
                padding: 12px;
            }
            
            .send-button,
            .clear-button {
                padding: 13px 24px;
                font-size: 15px;
            }
        }

        @media (max-width: 768px) {
            html {
                height: -webkit-fill-available;
            }
            body {
                height: 100vh;
                height: -webkit-fill-available;
                position: fixed;
                overflow: hidden;
            }
            .chat-container { 
                padding: 10px; 
                height: 100%;
                overflow: hidden;
            }
            .messages-container {
                flex: 1;
                overflow: hidden;
                border-radius: 12px;
            }
            .messages {
                height: 100%;
                overflow-y: auto;
                overflow-x: hidden;
                -webkit-overflow-scrolling: touch;
                padding: 12px;
            }
            .header { padding: 12px 14px; margin-bottom: 12px; border-radius: 14px; }
            .header-top-row { gap: 10px; margin-bottom: 8px; }
            .header-right { gap: 8px; }
            .icon-container { padding: 6px; border-radius: 8px; }
            .logo-img { width: 38px; height: 38px; }
            .title { font-size: 16px; }
            .subtitle { font-size: 10px; }
            .theme-toggle { padding: 7px; font-size: 16px; min-width: 36px; min-height: 36px; }
            .header-left-buttons { gap: 6px; }
            .back-button { padding: 5px 8px; font-size: 10px; gap: 3px; white-space: nowrap; }
            .description-line1 { font-size: 10px; line-height: 1.3; margin-bottom: 5px; }
            .description-line2 { font-size: 10px; line-height: 1.3; }
            .welcome-message { padding: 10px 10px 15px 10px; }
            .welcome-title { font-size: 18px; margin-bottom: 4px; }
            .welcome-text { font-size: 12px; line-height: 1.5; }
            .message { margin-bottom: 10px; }
            .message-icon { width: 32px; height: 32px; font-size: 16px; min-width: 32px; }
            .message-content { max-width: 80%; padding: 10px 14px; font-size: 13px; line-height: 1.5; }
            .quick-questions { grid-template-columns: 1fr; gap: 8px; padding: 12px; }
            .quick-question { padding: 10px 14px; font-size: 13px; border-radius: 10px; }
            .input-container { padding: 12px; gap: 10px; border-radius: 16px; flex-direction: column; flex-shrink: 0; }
            .voice-button { font-size: 18px; left: 10px; }
            .buttons-row { display: flex; gap: 10px; width: 100%; }
            .send-button, .clear-button { flex: 1; padding: 14px 20px; font-size: 15px; border-radius: 12px; font-weight: 600; min-height: 48px; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
        }
    </style>
</head>
<body class="light-mode">
    <div class="chat-container">
        <div class="header">
            <div class="header-top-row">
                <div class="header-left-buttons">
                    <button class="theme-toggle" onclick="toggleTheme()" title="تبديل الوضع">
                        <span id="themeIcon">🌙</span>
                    </button>
                    <a href="https://www.sawtalhaq.com/" class="back-button" title="العودة إلى صوت الحق" target="_blank">
                        <span>🏠</span>
                        <span>العودة إلى صوت الحق</span>
                    </a>
                </div>
                <div class="header-right">
                    <div class="icon-container">
                        <img src="/static/logo.jpeg" alt="اسأل صوت الحق" class="logo-img">
                    </div>
                    <div class="title-section">
                        <div class="title">اسأل صوت الحق</div>
                        <div class="subtitle">
                            <span class="status-dot"></span>
                            <span>آخر الأخبار</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="description-line1">
                المساعد الإخباري الذكي الذي يقدم لك أحدث الأخبار المحلية والعالمية بسرعة ودقة
            </div>
            <div class="description-line2">
                مدعوماً بالذكاء الاصطناعي
            </div>
        </div>

        <div class="messages-container">
            <div class="messages" id="messages">
                <div class="message assistant">
                    <div class="message-icon">
                        <img src="/static/logo.jpeg" alt="صوت الحق" class="logo-img">
                    </div>
                    <div class="message-content">
                        <strong>أهلاً بك!</strong><br>
                        معك نبأ - مساعدتك الرقمية في صوت الحق<br>
                        كيف يمكنني مساعدتك اليوم؟
                    </div>
                </div>

                <div class="quick-questions">
                    <div class="quick-question" onclick="askQuestion('آخر الأخبار المحلية في الأردن اليوم')">
                        آخر الأخبار المحلية اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('أحوال الطقس في الأردن اليوم')">
                        أحوال الطقس في الأردن اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('آخر الأخبار العالمية اليوم')">
                        آخر الأخبار العالمية اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('أسعار العملات والأسهم في الأردن اليوم')">
                        أسعار العملات والأسهم في الأردن اليوم
                    </div>
                </div>
            </div>

            <div class="loading" id="loading">
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
                <span class="loading-text" id="loadingText">جاري البحث في صوت الحق...</span>
            </div>

            <div class="input-container">
                <div class="input-wrapper">
                    <input
                        type="text"
                        id="messageInput"
                        class="input-field"
                        placeholder="اسأل عن أي شيء ..."
                        onkeypress="handleKeyPress(event)"
                    >
                    <button class="voice-button" id="voiceButton" onclick="toggleVoiceSearch()" title="بحث صوتي">
                        🎤
                    </button>
                </div>
                <div class="buttons-row">
                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        إرسال
                    </button>
                    <button class="clear-button" onclick="clearChat()">
                        دردشة جديدة
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const savedTheme = localStorage.getItem('theme') || 'light-mode';
        document.body.className = savedTheme;
        updateThemeIcon();

        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.classList.contains('light-mode') ? 'light-mode' : 'dark-mode';
            const newTheme = currentTheme === 'light-mode' ? 'dark-mode' : 'light-mode';

            body.classList.remove(currentTheme);
            body.classList.add(newTheme);

            localStorage.setItem('theme', newTheme);
            updateThemeIcon();
        }

        function updateThemeIcon() {
            const themeIcon = document.getElementById('themeIcon');
            const isDark = document.body.classList.contains('dark-mode');
            themeIcon.textContent = isDark ? '☀️' : '🌙';
        }

        function askQuestion(question) {
            document.getElementById('messageInput').value = question;
            sendMessage();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function clearChat() {
            const messages = document.getElementById('messages');
            messages.innerHTML = `
                <div class="message assistant">
                    <div class="message-icon">
                        <img src="/static/logo.jpeg" alt="صوت الحق" class="logo-img">
                    </div>
                    <div class="message-content">
                        <strong>أهلاً بك!</strong><br>
                        معك نبأ - مساعدتك الرقمية في صوت الحق<br>
                        كيف يمكنني مساعدتك اليوم؟
                    </div>
                </div>

                <div class="quick-questions">
                    <div class="quick-question" onclick="askQuestion('آخر الأخبار المحلية في الأردن اليوم')">
                        آخر الأخبار المحلية اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('أحوال الطقس في الأردن اليوم')">
                        أحوال الطقس في الأردن اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('آخر الأخبار العالمية اليوم')">
                        آخر الأخبار العالمية اليوم
                    </div>
                    <div class="quick-question" onclick="askQuestion('أسعار العملات والأسهم في الأردن اليوم')">
                        أسعار العملات والأسهم في الأردن اليوم
                    </div>
                </div>
            `;
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();

            if (!message) return;

            const firstMessage = document.querySelector(".message.assistant");
            const quickQuestions = document.querySelector(".quick-questions");
            if (firstMessage) firstMessage.style.display = "none";
            if (quickQuestions) quickQuestions.style.display = "none";

            addMessage(message, 'user');
            input.value = '';

            const loading = document.getElementById('loading');
            const loadingText = document.getElementById('loadingText');
            const sendButton = document.getElementById('sendButton');
            loading.classList.add('show');
            sendButton.disabled = true;

            const loadingMessages = [
                'جاري البحث في صوت الحق...',
                'أبحث عن أحدث الأخبار...',
                'أقرأ التفاصيل من الموقع...',
                'أجمع البيانات...'
            ];
            let msgIndex = 0;
            const loadingInterval = setInterval(() => {
                loadingText.textContent = loadingMessages[msgIndex];
                msgIndex = (msgIndex + 1) % loadingMessages.length;
            }, 1500);

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message
                    }),
                });

                const data = await response.json();

                clearInterval(loadingInterval);

                if (data.success) {
                    addMessage(
                        data.response,
                        'assistant',
                        data.searched,
                        data.sources
                    );
                } else {
                    addMessage('عذراً، حدث خطأ: ' + (data.error || 'غير معروف'), 'assistant');
                }
            } catch (error) {
                clearInterval(loadingInterval);
                addMessage('عذراً، حدث خطأ في الاتصال بالخادم', 'assistant');
            } finally {
                loading.classList.remove('show');
                sendButton.disabled = false;
                input.focus();
            }
        }


        function escapeHtml(str) {
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        function linkify(text) {
            const urlPattern = /(https?:\/\/[^\s<]+)/g;
            return text.replace(urlPattern, '<a href="$1" target="_blank" style="color: #B90000; text-decoration: underline;">$1</a>');
        }

        function formatText(text) {
            return linkify(escapeHtml(text)).replace(/\n/g, '<br>');
        }

        function addMessage(text, type, searched = false, sources = null) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            let searchBadge = '';
            let sourcesHtml = '';

            if (type === 'assistant' && searched) {
                searchBadge = '<div class="search-info">تم البحث في صوت الحق</div>';

                if (sources && sources.length > 0) {
                    sourcesHtml = '<div class="sources"><div class="source-title">المصادر:</div>';
                    sources.forEach(source => {
                        sourcesHtml += `<a href="${escapeHtml(source.url)}" target="_blank" class="source-link">
                            🔗 ${escapeHtml(source.title)}
                        </a>`;
                    });
                    sourcesHtml += '</div>';
                }
            }

            const iconHTML = type === 'user' ? '👤' : '<img src="/static/logo.jpeg" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">';

            messageDiv.innerHTML = `
                <div class="message-icon">${iconHTML}</div>
                <div class="message-content">
                    ${searchBadge}
                    ${formatText(text)}
                    ${sourcesHtml}
                </div>
            `;

            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('messageInput').focus();
        });

        // البحث الصوتي
        let recognition = null;
        let isRecording = false;

        function toggleVoiceSearch() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert('عذراً، المتصفح الخاص بك لا يدعم البحث الصوتي. جرب Chrome أو Edge.');
                return;
            }

            if (!recognition) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.lang = 'ar-SA'; // اللغة العربية (السعودية)
                recognition.continuous = false;
                recognition.interimResults = false;

                recognition.onstart = function() {
                    isRecording = true;
                    const voiceButton = document.getElementById('voiceButton');
                    voiceButton.classList.add('recording');
                    document.getElementById('messageInput').placeholder = '🎤 جاري الاستماع...';
                };

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('messageInput').value = transcript;
                    isRecording = false;
                    const voiceButton = document.getElementById('voiceButton');
                    voiceButton.classList.remove('recording');
                    document.getElementById('messageInput').placeholder = 'اسأل عن أي شيء ...';
                };

                recognition.onerror = function(event) {
                    console.error('خطأ في التعرف على الصوت:', event.error);
                    isRecording = false;
                    const voiceButton = document.getElementById('voiceButton');
                    voiceButton.classList.remove('recording');
                    document.getElementById('messageInput').placeholder = 'اسأل عن أي شيء ...';
                    
                    if (event.error === 'no-speech') {
                        alert('لم يتم اكتشاف أي صوت. حاول مرة أخرى.');
                    } else if (event.error === 'not-allowed') {
                        alert('الرجاء السماح بالوصول إلى الميكروفون.');
                    }
                };

                recognition.onend = function() {
                    isRecording = false;
                    const voiceButton = document.getElementById('voiceButton');
                    voiceButton.classList.remove('recording');
                    document.getElementById('messageInput').placeholder = 'اسأل عن أي شيء ...';
                };
            }

            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
    </script>
</body>
</html>
'''

# ====================== البحث داخل موقع صوت الحق فقط (بدون أي ذكاء اصطناعي) ======================
BASE_URL = 'https://www.sawtalhaq.com'
URL_RSS = BASE_URL + '/rss.xml'
URL_LATEST = BASE_URL + '/latest'
URL_WEATHER = BASE_URL + '/weather'
URL_SPORT = BASE_URL + '/sport'
URL_BOURSE = BASE_URL + '/bourse'
URL_CAT_JORDAN = BASE_URL + '/category-101/%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1-%D8%A7%D9%84%D8%A7%D8%B1%D8%AF%D9%86'
URL_CAT_WORLD = BASE_URL + '/category-7/%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1-%D8%B9%D8%A7%D9%84%D9%85%D9%8A%D8%A9'
URL_CAT_ECONOMY = BASE_URL + '/category-5/%D8%A7%D9%82%D8%AA%D8%B5%D8%A7%D8%AF'
URL_CAT_SPORT = BASE_URL + '/category-9/%D8%B1%D9%8A%D8%A7%D8%B6%D8%A9'

try:
    JORDAN_TZ = ZoneInfo("Asia/Amman")
except Exception:
    JORDAN_TZ = timezone(timedelta(hours=3))

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.8'
}

_cache = {}
CACHE_TTL = 300  # 5 دقائق


def fetch_url(url, ttl=CACHE_TTL):
    """جلب صفحة مع كاش بسيط"""
    now = time.time()
    if url in _cache and now - _cache[url][0] < ttl:
        return _cache[url][1]
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=10)
        if r.status_code == 200:
            r.encoding = 'utf-8'
            _cache[url] = (now, r.text)
            return r.text
        print(f"فشل جلب {url}: الحالة {r.status_code}")
    except Exception as e:
        print(f"خطأ في جلب {url}: {e}")
    return None


# ---------- معالجة النص العربي ----------
def normalize_ar(text):
    """توحيد الحروف العربية للمقارنة"""
    text = re.sub(r'[\u064B-\u0652\u0640]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text.lower()


def stem_ar(word):
    word = normalize_ar(word)
    for prefix in ('وال', 'بال', 'لل', 'ال'):
        if word.startswith(prefix) and len(word) - len(prefix) >= 3:
            return word[len(prefix):]
    return word


_STOP_WORDS = [
    'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
    'التي', 'الذي', 'الذين', 'هو', 'هي', 'هم', 'نحن', 'أنا',
    'ما', 'ماذا', 'متى', 'أين', 'كيف', 'لماذا', 'هل', 'كم',
    'كان', 'كانت', 'يكون', 'لم', 'لن', 'لا', 'ليس', 'غير', 'إلا',
    'قد', 'لقد', 'قبل', 'بعد', 'عند', 'لدى', 'حول', 'خلال',
    'ثم', 'أو', 'لكن', 'بل', 'إن', 'أن', 'لأن',
    'اليوم', 'أمس', 'غدا', 'الآن', 'حاليا', 'مؤخرا',
    'أي', 'كل', 'جميع', 'بعض', 'آخر', 'أول', 'أحدث', 'جديد',
    'اريد', 'بدي', 'ابي', 'شو', 'وين', 'عن', 'اخبرني', 'اعطني', 'اعرض'
]
STOP_STEMS = {stem_ar(w) for w in _STOP_WORDS}

GENERIC_STEMS = {
    'اخبار', 'خبر', 'محليه', 'محلي', 'عالميه', 'عالمي', 'اردن', 'اردني',
    'اردنيه', 'معلومات', 'تفاصيل', 'مباراه', 'مباريات', 'رياضه', 'رياضي',
    'رياضيه', 'طقس', 'احوال', 'حاله', 'جدول', 'نتائج', 'نتايج', 'نتيجه'
}


def get_query_keywords(query):
    """الكلمات المفتاحية للبحث (بعد إزالة الكلمات الشائعة)"""
    tokens = re.findall(r'[\u0621-\u0652A-Za-z0-9]+', query)
    out = []
    for t in tokens:
        s = stem_ar(t)
        if len(s) > 2 and s not in STOP_STEMS and s not in GENERIC_STEMS:
            out.append(s)
    return out


_SPORT_STEMS = {stem_ar(k) for k in [
    'رياضة', 'رياضي', 'رياضية', 'الرياضة', 'كرة', 'القدم', 'السلة', 'الطائرة',
    'مباراة', 'مباريات', 'بطولة', 'دوري', 'كأس', 'لاعب', 'لاعبين', 'مدرب',
    'ملعب', 'رونالدو', 'ميسي', 'صلاح', 'نادي', 'أندية', 'ريال', 'برشلونة',
    'ليفربول', 'الوحدات', 'الفيصلي', 'الأهلي', 'الهلال', 'منتخب', 'النشامى',
    'أولمبياد', 'سباحة', 'ملاكمة', 'تنس', 'فورمولا', 'ufc', 'نيمار', 'مبابي',
    'هالاند', 'كريستيانو', 'الوداد', 'الرمثا', 'الجزيرة', 'الحسين', 'جدول المباريات'
]}


def is_sports_query(text):
    """التحقق إذا كان السؤال عن الرياضة (مطابقة كلمة كاملة)"""
    tokens = re.findall(r'[\u0621-\u0652A-Za-z0-9]+', text)
    return any(stem_ar(t) in _SPORT_STEMS for t in tokens)


# ---------- الوقت ----------
def format_date(value):
    if not value:
        return ''
    try:
        if re.match(r'\d{4}-\d{2}-\d{2}', value):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=JORDAN_TZ)
        return dt.astimezone(JORDAN_TZ).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return ''


# ---------- جمع الأخبار من الموقع ----------
def parse_rss(xml_text):
    items = []
    if not xml_text:
        return items
    try:
        root = ET.fromstring(xml_text.encode('utf-8'))
        for it in root.iter('item'):
            items.append({
                'title': (it.findtext('title') or '').strip(),
                'url': (it.findtext('link') or '').strip(),
                'desc': (it.findtext('description') or '').strip(),
                'date': (it.findtext('pubDate') or '').strip()
            })
    except Exception as e:
        print(f"خطأ في RSS: {e}")
    return items


def get_rss_items():
    return parse_rss(fetch_url(URL_RSS))


def parse_listing(html, page_url, widget_urls=None):
    """استخراج روابط الأخبار من صفحة قسم، مع تجاهل ودجت (آخر الأخبار) المكرر بكل صفحة"""
    soup = BeautifulSoup(html, 'html.parser')
    root = soup.find('main') or soup
    ordered, seen = [], set()
    for a in root.select('a[href*="/news/"]'):
        url = urljoin(page_url, a.get('href', '')).split('#')[0]
        heading = a.find(['h1', 'h2', 'h3', 'h4'])
        title = (heading or a).get_text(' ', strip=True)
        if len(title) < 15 or url in seen:
            continue
        seen.add(url)
        ordered.append({'title': title, 'url': url, 'desc': '', 'date': ''})

    n = len(widget_urls or [])
    if n and len(ordered) > n and {i['url'] for i in ordered[:n]} == set(widget_urls):
        ordered = ordered[n:]
    return ordered


def get_category_items(url):
    html = fetch_url(url)
    if not html:
        return []
    widget = [it['url'] for it in get_rss_items()[:10]]
    return parse_listing(html, url, widget)


def get_news_pool(extra_pages=()):
    """تجميع الأخبار من RSS + آخر الأخبار + الأقسام المطلوبة"""
    rss_items = get_rss_items()
    widget = [it['url'] for it in rss_items[:10]]
    pool, seen = [], set()

    def add(items):
        for it in items:
            if it['url'] and it['url'] not in seen:
                seen.add(it['url'])
                pool.append(it)

    add(rss_items)
    for page in (URL_LATEST,) + tuple(extra_pages):
        html = fetch_url(page)
        if html:
            add(parse_listing(html, page, widget))
    return pool


def score_item(item, keywords):
    title = normalize_ar(item['title'])
    desc = normalize_ar(item.get('desc', ''))
    return sum((2 if k in title else 0) + (1 if k in desc else 0) for k in keywords)


def pick_items(pool, keywords, limit=4):
    if not keywords:
        return pool[:limit]
    scored = [(score_item(it, keywords), i, it) for i, it in enumerate(pool)]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [s[2] for s in scored[:limit]]


def summarize(text, limit=450):
    text = re.sub(r'\s+', ' ', text or '').strip()
    text = re.sub(r'^صوت الحق\s*:?\s*-?\s*', '', text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0] + '…'


def fetch_article(item):
    """جلب نص الخبر الكامل من صفحته"""
    html = fetch_url(item['url'], ttl=900)
    result = {'title': item['title'], 'url': item['url'],
              'desc': item.get('desc', ''), 'date': item.get('date', '')}
    if not html:
        return result
    soup = BeautifulSoup(html, 'html.parser')

    def meta(prop):
        tag = soup.find('meta', attrs={'property': prop}) or soup.find('meta', attrs={'name': prop})
        return tag.get('content', '').strip() if tag else ''

    title = meta('og:title')
    if not title and soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)
    if title:
        result['title'] = re.sub(r'\s*[\|\-–—]\s*صوت الحق.*$', '', title).strip()
    result['date'] = meta('article:published_time') or result['date']

    for t in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        t.decompose()
    container = soup.find('article') or soup
    paragraphs = []
    for p in container.find_all('p'):
        txt = p.get_text(' ', strip=True)
        if len(txt) > 30 and 'جميع الحقوق' not in txt and 'منصة إخبارية تفاعلية' not in txt:
            paragraphs.append(txt)
    body = ' '.join(paragraphs)
    if len(body) < 80:
        body = meta('og:description') or result['desc']
    result['desc'] = body
    return result


def short_title(title):
    return title[:50] + '...' if len(title) > 50 else title


def format_article(i, a):
    lines = [f"{i}) {a['title']}"]
    d = format_date(a.get('date'))
    if d:
        lines.append(f"🕒 {d}")
    s = summarize(a.get('desc', ''))
    if s:
        lines.append(s)
    return '\n'.join(lines)


def articles_block(items, sources, title_line):
    """يجلب الأخبار بالتوازي ويرجع نصاً منسقاً"""
    if not items:
        return ''
    with ThreadPoolExecutor(max_workers=4) as ex:
        articles = list(ex.map(fetch_article, items))
    blocks = []
    for i, a in enumerate(articles, 1):
        blocks.append(format_article(i, a))
        sources.append({'title': short_title(a['title']), 'url': a['url']})
    return title_line + '\n\n' + '\n\n'.join(blocks)


# ---------- الطقس (من صفحة /weather) ----------
_GOVS = ['عمّان', 'إربد', 'الزرقاء', 'البلقاء', 'مأدبا', 'الكرك', 'الطفيلة',
         'معان', 'العقبة', 'جرش', 'عجلون', 'المفرق']
_GOV_MAP = {normalize_ar(g): g for g in _GOVS}
_DAYS = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']


def parse_weather(html):
    soup = BeautifulSoup(html, 'html.parser')
    for t in soup(['script', 'style', 'noscript']):
        t.decompose()
    lines = [l.strip() for l in soup.get_text('\n').split('\n') if l.strip()]
    start = next((i for i, l in enumerate(lines) if 'كافة محافظات المملكة' in l), 0)
    lines = lines[start + 1:]

    govs, cur = {}, None
    for l in lines:
        key = normalize_ar(l)
        if key in _GOV_MAP and len(l) < 12:
            cur = {'name': _GOV_MAP[key], 'raw': []}
            govs[key] = cur
            continue
        if cur is not None:
            cur['raw'].append(l)

    for g in govs.values():
        raw = g['raw']
        idx = next((i for i, l in enumerate(raw) if 'توقعات' in l), len(raw))
        head_lines, tail_lines = raw[:idx], raw[idx + 1:]
        head = ' '.join(head_lines)
        g['cond'] = next((l for l in head_lines
                          if not re.search(r'\d|رياح|رطوبة|•', l)), '')
        m = re.search(r'رياح:\s*([\d.]+)', head)
        g['wind'] = m.group(1) if m else ''
        m = re.search(r'رطوبة:\s*(\d+)\s*%', head)
        g['hum'] = m.group(1) if m else ''
        m = re.search(r'(-?\d+)\s*°', head)
        g['temp'] = m.group(1) if m else ''

        days, day = [], None
        for l in tail_lines:
            if l in _DAYS:
                day = {'day': l, 'temps': []}
                days.append(day)
            elif day is not None:
                day['temps'] += re.findall(r'-?\d+', l.replace('°', ' ')) if '°' in l else []
        g['days'] = [d for d in days if d['temps']]
    return govs


def format_gov(g, with_days=True):
    lines = [f"📍 {g['name']}: {g['temp']}° — {g['cond']}".rstrip(' —')]
    extra = []
    if g['wind']:
        extra.append(f"🌬 الرياح {g['wind']} كم/س")
    if g['hum']:
        extra.append(f"💧 الرطوبة {g['hum']}%")
    if extra:
        lines.append('   ' + ' | '.join(extra))
    if with_days and g['days']:
        for d in g['days']:
            t = d['temps']
            if len(t) >= 2:
                lines.append(f"   • {d['day']}: عظمى {t[0]}° / صغرى {t[1]}°")
            else:
                lines.append(f"   • {d['day']}: {t[0]}°")
    return '\n'.join(lines)


# ---------- الرياضة (من صفحة /sport) ----------
_SCORE_RE = re.compile(r"^(?:\d+'\s*)?\d+\s*-\s*\d+$|^\d{1,2}:\d{2}\s*[صم]$")


def find_matches(keywords, limit=6):
    """البحث عن فريق داخل جدول المباريات"""
    html = fetch_url(URL_SPORT)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    for t in soup(['script', 'style', 'noscript']):
        t.decompose()
    lines = [l.strip() for l in soup.get_text('\n').split('\n') if l.strip()]

    found, seen = [], set()
    for i, l in enumerate(lines):
        if len(l) > 40 or not any(k in normalize_ar(l) for k in keywords):
            continue
        row = None
        if i + 2 < len(lines) and _SCORE_RE.match(lines[i + 1]):
            row = (l, lines[i + 1], lines[i + 2])
        elif i >= 2 and _SCORE_RE.match(lines[i - 1]):
            row = (lines[i - 2], lines[i - 1], l)
        if row and row not in seen:
            seen.add(row)
            found.append(f"• {row[0]}  {row[1]}  {row[2]}")
        if len(found) >= limit:
            break
    return found


# ---------- بناء الجواب ----------
def search_sawtalhaq(query):
    """يرجع (نص الجواب، المصادر) من موقع صوت الحق فقط"""
    q = normalize_ar(query)
    keywords = get_query_keywords(query)
    sources, parts = [], []

    is_weather = any(w in q for w in ['طقس', 'حراره', 'امطار', 'مطر', 'الجو', 'درجات', 'ثلج', 'منخفض جوي'])
    is_sport = (not is_weather) and is_sports_query(query)
    is_world = any(w in q for w in ['عالمي', 'دولي', 'عربي', 'العالم'])
    is_economy = any(w in q for w in ['اقتصاد', 'ذهب', 'اسعار', 'عملات', 'اسهم', 'بورصه', 'دينار', 'دولار', 'مؤشر'])

    header = 'وفقاً لصوت الحق، هذه آخر الأخبار:'

    if is_weather:
        header = 'وفقاً لصوت الحق، هذه حالة الطقس:'
        html = fetch_url(URL_WEATHER)
        govs = parse_weather(html) if html else {}
        if govs:
            wanted = [g for k, g in govs.items() if k in q]
            if wanted:
                parts.append('\n\n'.join(format_gov(g, True) for g in wanted))
            else:
                main = govs.get('عمان') or next(iter(govs.values()))
                parts.append(format_gov(main, True))
                others = [format_gov(g, False).split('\n')[0] for k, g in govs.items() if g is not main]
                if others:
                    parts.append('باقي المحافظات الآن:\n' + '\n'.join(others))
            sources.append({'title': 'حالة الطقس في الأردن — صوت الحق', 'url': URL_WEATHER})
        pool = get_news_pool()
        related = pick_items(pool, ['طقس', 'حراره', 'امطار', 'مطر', 'منخفض'], limit=2)
        block = articles_block(related, sources, '🌦 آخر أخبار الطقس:')
        if block:
            parts.append(block)

    elif is_sport:
        sources.append({'title': 'الرياضة وجدول المباريات — صوت الحق', 'url': URL_SPORT})
        header = 'وفقاً لصوت الحق، هذه آخر الأخبار الرياضية:'
        if keywords:
            header = 'وفقاً لصوت الحق، وجدت هذه النتائج المتعلقة بسؤالك:'
            matches = find_matches(keywords)
            if matches:
                parts.append('⚽ من جدول المباريات:\n' + '\n'.join(matches))
            pool = get_news_pool(extra_pages=(URL_CAT_SPORT,))
            related = pick_items(pool, keywords, limit=4)
        else:
            parts.append('📅 جدول المباريات والنتائج المباشرة متوفر في صفحة الرياضة (الرابط أدناه).')
            related = get_category_items(URL_CAT_SPORT)[:4]
        block = articles_block(related, sources, '🏆 أخبار رياضية:')
        if block:
            parts.append(block)

    else:
        if is_world:
            cat = URL_CAT_WORLD
        elif is_economy:
            cat = URL_CAT_ECONOMY
        else:
            cat = URL_CAT_JORDAN

        if keywords:
            header = 'وفقاً لصوت الحق، وجدت هذه الأخبار المتعلقة بسؤالك:'
            related = pick_items(get_news_pool(extra_pages=(cat,)), keywords, limit=4)
        else:
            related = get_category_items(cat)[:5] or get_news_pool()[:5]

        if any(w in q for w in ['بورصه', 'اسهم', 'مؤشر']):
            parts.append('📈 تفاصيل التداول والمؤشرات في صفحة بورصة عمّان (الرابط أدناه).')
            sources.append({'title': 'بورصة عمّان — صوت الحق', 'url': URL_BOURSE})

        block = articles_block(related, sources, '📰 الأخبار:')
        if block:
            parts.append(block)

    if parts:
        return header + '\n\n' + '\n\n'.join(parts), sources

    # لا نتائج
    latest = get_news_pool()[:3]
    if latest:
        titles = '\n'.join(f"• {it['title']}" for it in latest)
        text = ('وفقاً لصوت الحق، لم أجد خبراً مطابقاً لسؤالك ضمن الأخبار المنشورة مؤخراً.\n'
                'جرّب كلمات أخرى، أو اطّلع على آخر الأخبار:\n\n' + titles)
        srcs = [{'title': short_title(it['title']), 'url': it['url']} for it in latest]
        srcs.append({'title': 'آخر الأخبار — صوت الحق', 'url': URL_LATEST})
        return text, srcs
    return ('تعذر الوصول إلى موقع صوت الحق حالياً، حاول مرة أخرى بعد قليل.',
            [{'title': 'صوت الحق', 'url': BASE_URL}])


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'الرجاء إدخال سؤال'
            })

        print(f"السؤال: {user_message}")

        response_text, sources = search_sawtalhaq(user_message)
        error, searched = None, True

        if response_text:
            return jsonify({
                'success': True,
                'response': response_text,
                'searched': searched,
                'sources': sources
            })
        else:
            return jsonify({
                'success': False,
                'error': error or 'حدث خطأ في الحصول على الرد'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'حدث خطأ: {str(e)}'
        })

@app.route('/health')
def health():
    """فحص سريع: هل يستطيع السيرفر الوصول لصفحات موقع صوت الحق؟"""
    report = {}
    for name, url in [('rss', URL_RSS), ('latest', URL_LATEST), ('weather', URL_WEATHER), ('sport', URL_SPORT)]:
        html = fetch_url(url, ttl=0)
        report[name] = f'OK ({len(html)} حرف)' if html else 'فشل'
    report['news_items'] = len(get_news_pool())
    html = fetch_url(URL_WEATHER)
    report['weather_governorates'] = len(parse_weather(html)) if html else 0
    return jsonify(report)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print("=" * 80)
    print("اسأل صوت الحق - البحث من موقع sawtalhaq.com فقط (بدون ذكاء اصطناعي)")
    print("=" * 80)
    print(f"افتح المتصفح على: http://localhost:{port}")
    print(f"فحص الاتصال بالموقع: http://localhost:{port}/health")
    print("=" * 80)
    app.run(host='0.0.0.0', port=port, debug=False)
