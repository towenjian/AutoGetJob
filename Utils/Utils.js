/**
 * EnvironmentProxyMonitor 类：用于智能监控和记录对指定对象及其属性的访问。
 * 支持代理已存在的对象，并保留其原生功能。
 */
class EnvironmentProxyMonitor {
    constructor() {
        // 存储所有监控到的访问记录
        this.log = [];
        // 存储变量名到其访问日志的映射
        this.variableLogs = {};
        // 标记，用于区分不同类型的日志输出
        this.ACTION_MAP = {
            GET: { color: '#007bff', label: '读取属性' },
            SET: { color: '#20c997', label: '设置属性' },
            CALL: { color: '#dc3545', label: '调用方法' },
            NEW: { color: '#ffc107', label: '构造实例' },
            MISSING_GET: { color: '#6f42c1', label: '缺失属性' }
        };
    }

    /**
     * 记录并输出访问日志
     * @param {string} variableName 根变量名
     * @param {string} fullPath 完整的属性访问路径
     * @param {string} action 访问动作 (GET, SET, CALL, NEW, MISSING_GET)
     * @param {*} value 访问后获取或设置的值
     */
    _record(variableName, fullPath, action, value) {
        const actionInfo = this.ACTION_MAP[action];
        const valueType = typeof value;

        const record = {
            variable: variableName,
            path: fullPath,
            action: action,
            valueType: valueType,
            value: (valueType === 'object' || valueType === 'function') ? `[${valueType}]` : String(value),
            timestamp: Date.now()
        };
        this.log.push(record);
        if (!this.variableLogs[variableName]) {
            this.variableLogs[variableName] = [];
        }

        // 避免重复记录相同的 GET 访问路径，但 CALL 和 SET 每次都记录
        const isDuplicateGet = action === 'GET' && this.variableLogs[variableName].some(r => r.path === fullPath && r.action === 'GET');
        if (!isDuplicateGet) {
             this.variableLogs[variableName].push(record);
        }

        // 格式化输出到控制台 (使用 CSS 方便查看)
        console.log(
            `%c方法: ${action}%c | 对象: %c${variableName}%c | 属性: %c${fullPath}%c | 属性值类型: %c${valueType}%c`,
            `color: ${actionInfo.color}; font-weight: bold;`, 'color: black;',
            'color: #007bff; font-weight: bold;', 'color: black;',
            'color: #28a745; font-style: italic;', 'color: black;',
            'color: #dc3545; font-weight: bold;'
        );
    }

    /**
     * 创建一个递归代理对象来监控访问。
     * @param {string} variableName 根变量名
     * @param {string} currentPath 当前路径
     * @param {object} targetObj 原始对象 (如果是模拟环境，则为 {})
     * @returns {Proxy} 代理对象
     */
    _createRecursiveProxy(variableName, currentPath, targetObj) {

        const self = this;

        const handler = {
            // 捕获属性读取 (obj.prop)
            get(target, prop, receiver) {
                const propName = String(prop);
                const nextPath = `${currentPath}.${propName}`;

                // 忽略内部属性
                if (typeof prop === 'symbol' || ['toString', 'constructor', 'name'].includes(propName)) {
                    if (propName === 'toString') return () => `[Monitored Proxy for ${currentPath}]`;
                    return Reflect.get(target, prop, receiver);
                }

                // 1. 尝试获取原始值
                const originalValue = Reflect.get(target, prop, receiver);

                // 2. 如果原始值存在，并且不是基本类型 (是对象或函数)，则返回其代理
                if (originalValue !== undefined && originalValue !== null && (typeof originalValue === 'object' || typeof originalValue === 'function')) {
                    self._record(variableName, nextPath, 'GET', originalValue);
                    // 递归代理原始值，保留原生功能
                    return self._createRecursiveProxy(variableName, nextPath, originalValue);
                }

                // 3. 如果原始值是基本类型 (string, number, boolean)，直接返回并记录
                if (originalValue !== undefined) {
                    self._record(variableName, nextPath, 'GET', originalValue);
                    return originalValue;
                }

                // 4. 如果原始值不存在 (缺失)，返回一个新的占位代理（这是重点）
                self._record(variableName, nextPath, 'MISSING_GET', undefined);

                // 返回一个可被调用/访问的新代理，用于处理链式访问（如 aaa.b.c()）
                const placeholderProxy = self._createRecursiveProxy(variableName, nextPath, {});

                // 返回一个函数代理，使其可以被调用 (variable.func()) 或被 new (new variable.Class())
                return new Proxy(placeholderProxy, {
                    apply(target, thisArg, argumentsList) {
                        self._record(variableName, nextPath, 'CALL', 'function');
                        return self._createRecursiveProxy(variableName, `${nextPath}()`, {});
                    },
                    construct(target, argumentsList) {
                        self._record(variableName, nextPath, 'NEW', 'object');
                        return self._createRecursiveProxy(variableName, `new ${nextPath}`, {});
                    }
                });
            },

            // 捕获属性设置 (obj.prop = value)
            set(target, prop, value, receiver) {
                const nextPath = `${currentPath}.${String(prop)}`;
                self._record(variableName, nextPath, 'SET', value);
                // 尝试设置到原始对象上，保留原生功能
                return Reflect.set(target, prop, value, receiver);
            },

            // 捕获 in 操作 ('prop' in obj)
            has(target, prop) {
                 // 假装属性存在
                 return true;
            }
        };

        // 返回目标对象的代理。如果目标是函数，则直接代理它；否则代理一个空对象，让 get 陷阱处理
        return new Proxy(targetObj || {}, handler);
    }

    /**
     * 启动监控并将代理对象注入到全局环境 (globalThis)。
     * @param {string[]} variableNames 需要监控的全局变量名称列表
     * @returns {object} 包含代理对象和日志报告的接口
     */
    startMonitoring(variableNames) {
        console.log(`\n================== 智能环境监控启动 (${variableNames.join(', ')}) ==================`);

        variableNames.forEach(name => {
            // 获取全局对象上可能存在的原始值，以便代理它
            const originalTarget = globalThis[name] || {};
            const proxy = this._createRecursiveProxy(name, name, originalTarget);

            // 注入到全局对象
            try {
                globalThis[name] = proxy;
                console.log(`[INFO] 成功注入代理变量: ${name} (代理目标: ${typeof originalTarget})`);
            } catch (e) {
                console.error(`[ERROR] 无法注入全局变量 '${name}'。`);
            }
        });

        return {
            getLog: () => this.log,
            getVariableLogs: () => this.variableLogs
        };
    }
}


/**
 * 导出函数：封装 EnvironmentProxyMonitor 的实例化和启动过程。
 * @param {string[]} proxyArray 需要监控的全局变量名称列表 (如 ['window', 'document', 'navigator'])
 * @returns {object} 包含日志报告方法的对象
 */
export function getMonitoredEnvironment(proxyArray) {
    const monitor = new EnvironmentProxyMonitor();
    return monitor.startMonitoring(proxyArray);
}

// -------------------------------------------------------------
// --- 模块导出 (根据您的环境选择) ---
// -------------------------------------------------------------

// 如果在 Node.js 或支持 CommonJS 的环境中使用
// module.exports = { getMonitoredEnvironment };

// 如果在浏览器或支持 ES Modules 的环境中使用
// export { getMonitoredEnvironment };

// -------------------------------------------------------------
// --- 示例用法 (请在你的目标代码前调用) ---
// -------------------------------------------------------------
/*
// 模拟您的代码：
// const proxy_array = ['window', 'document', 'location', 'navigator', 'history', 'screen', 'aaa', 'target'];
// const reporter = getMonitoredEnvironment(proxy_array);

// 假设 document 存在且有 title 属性
// document.title = 'Test'; // 触发 GET document -> GET document.title -> SET document.title
// document.notExist.method(); // 触发 MISSING_GET document.notExist -> CALL document.notExist.method()

// 获取最终报告:
// console.log(reporter.getVariableLogs().document);
*/