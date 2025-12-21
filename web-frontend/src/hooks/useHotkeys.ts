// hooks/useHotkeys.ts
// 全局快捷键Hook

import { useEffect } from 'react';

export interface HotkeyConfig {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  handler: () => void;
  description?: string;
}

export const useHotkeys = (configs: HotkeyConfig[]) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      for (const config of configs) {
        const ctrlMatch = config.ctrl ? (event.ctrlKey || event.metaKey) : true;
        const altMatch = config.alt ? event.altKey : !event.altKey;
        const shiftMatch = config.shift ? event.shiftKey : !event.shiftKey;
        const keyMatch = event.key.toLowerCase() === config.key.toLowerCase();

        if (ctrlMatch && altMatch && shiftMatch && keyMatch) {
          // 排除在输入框中的快捷键
          const target = event.target as HTMLElement;
          if (
            target.tagName === 'INPUT' ||
            target.tagName === 'TEXTAREA' ||
            target.isContentEditable
          ) {
            // 某些快捷键（如保存）在输入框中也应该生效
            if (!['s'].includes(config.key.toLowerCase())) {
              continue;
            }
          }

          event.preventDefault();
          config.handler();
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [configs]);
};

// 预定义的快捷键描述
export const HOTKEY_DESCRIPTIONS = {
  TOGGLE_SIDEBAR: 'Ctrl/Cmd + B - 切换侧边栏',
  TOGGLE_THEME: 'Ctrl/Cmd + D - 切换深色模式',
  SAVE: 'Ctrl/Cmd + S - 保存',
  COMMAND_PALETTE: 'Ctrl/Cmd + K - 打开命令面板',
  HELP: 'Ctrl/Cmd + / - 显示快捷键帮助',
};
