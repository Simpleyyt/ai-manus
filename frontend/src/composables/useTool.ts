import { computed, Ref } from 'vue';
import type { ToolContent } from '../types/message';
import { useI18n } from 'vue-i18n';
import { TOOL_ICON_MAP, TOOL_NAME_MAP, TOOL_FUNCTION_MAP, TOOL_FUNCTION_ARG_MAP, TOOL_COMPONENT_MAP } from '../constants/tool';

export function useToolInfo(tool?: Ref<ToolContent | undefined>) {
  const { t } = useI18n();

  const toolInfo = computed(() => {
    if (!tool || !tool.value) return null;
    
    // MCP tool
    if (tool.value.function.startsWith('mcp_')) {
      const mcpToolName = tool.value.function.replace(/^mcp_/, '');
      let functionArg = '';
      
      const args = tool.value.args;
      if (args && Object.keys(args).length > 0) {
        const firstKey = Object.keys(args)[0];
        const firstValue = args[firstKey];
        if (typeof firstValue === 'string' && firstValue.length < 50) {
          functionArg = firstValue;
        } else if (firstValue !== undefined) {
          functionArg = JSON.stringify(firstValue).substring(0, 30) + '...';
        }
      }
      
      return {
        icon: TOOL_ICON_MAP['mcp'] || null,
        name: t(TOOL_NAME_MAP['mcp'] || 'MCP Tool'),
        function: mcpToolName,
        functionArg: functionArg,
        view: TOOL_COMPONENT_MAP['mcp'] || null
      };
    }
    
    let functionArg = tool.value.args[TOOL_FUNCTION_ARG_MAP[tool.value.function]] || '';
    if (TOOL_FUNCTION_ARG_MAP[tool.value.function] === 'file') {
      functionArg = functionArg.replace(/^\/home\/ubuntu\//, '');
    }
    
    return {
      icon: TOOL_ICON_MAP[tool.value.name] || null,
      name: t(TOOL_NAME_MAP[tool.value.name] || ''),
      function: t(TOOL_FUNCTION_MAP[tool.value.function] || tool.value.function),
      functionArg: functionArg,
      view: TOOL_COMPONENT_MAP[tool.value.name] || null
    };
  });

  return {
    toolInfo
  };
} 