// Kanban admin extension for ToolRegistry Hub.
//
// Loaded by the admin shell through the extension contract v1:
//   import('…/assets/ext/board/main.js').then(m => m.register({container, api, i18n}))
//
// The module owns no authentication: every request goes through the shell's
// API client, which already carries the operator session.  Labels live here
// rather than in the shell dictionary, so the page ships its own EN/ZH map.

const STRINGS = {
    en: {
        'board.projects': 'Project',
        'board.newProject': 'New project',
        'board.refresh': 'Refresh',
        'board.projectPrompt': 'Project name for the new board',
        'board.loading': 'Loading…',
        'board.empty': 'No entries',
        'board.error': 'Request failed: {message}',
        'board.add': 'Add entry',
        'board.save': 'Save',
        'board.cancel': 'Cancel',
        'board.edit': 'Edit',
        'board.delete': 'Delete',
        'board.confirmDelete': 'Delete entry {id}? It is removed from the board but kept in the database.',
        'board.title': 'Title',
        'board.content': 'Content',
        'board.status': 'Status',
        'board.priority': 'Priority',
        'board.due': 'Due',
        'board.labels': 'Labels',
        'board.assignee': 'Assignee',
        'board.links': 'Links',
        'board.labelsHint': 'Comma separated',
        'board.linksHint': 'Comma separated http(s) URLs',
        'board.titleRequired': 'A title is required',
        'board.unassigned': 'Unassigned',
    },
    zh: {
        'board.projects': '项目',
        'board.newProject': '新建项目',
        'board.refresh': '刷新',
        'board.projectPrompt': '新看板的项目名称',
        'board.loading': '加载中…',
        'board.empty': '暂无条目',
        'board.error': '请求失败：{message}',
        'board.add': '新建条目',
        'board.save': '保存',
        'board.cancel': '取消',
        'board.edit': '编辑',
        'board.delete': '删除',
        'board.confirmDelete': '删除条目 {id}？它会从看板移除，但保留在数据库中。',
        'board.title': '标题',
        'board.content': '内容',
        'board.status': '状态',
        'board.priority': '优先级',
        'board.due': '截止日',
        'board.labels': '标签',
        'board.assignee': '负责人',
        'board.links': '链接',
        'board.labelsHint': '逗号分隔',
        'board.linksHint': '逗号分隔的 http(s) 链接',
        'board.titleRequired': '标题不能为空',
        'board.unassigned': '未指派',
    },
};

const COLUMNS = ['backlog', 'todo', 'in_progress', 'done', 'cancelled'];
const COLUMN_LABELS = {
    en: {
        backlog: 'Backlog',
        todo: 'To do',
        in_progress: 'In progress',
        done: 'Done',
        cancelled: 'Cancelled',
    },
    zh: {
        backlog: '待办池',
        todo: '待开始',
        in_progress: '进行中',
        done: '已完成',
        cancelled: '已取消',
    },
};
const PRIORITIES = ['urgent', 'high', 'medium', 'low'];

let root = null;
let client = null;
let onLanguageChange = null;
const state = {
    lang: 'en',
    project: '',
    projects: [],
    columns: [],
    error: '',
    editing: null, // {mode: 'create'|'edit', status, entry?}
};

// ---------------------------------------------------------------- helpers

function t(key, vars) {
    const table = STRINGS[state.lang] || STRINGS.en;
    let text = table[key] || STRINGS.en[key] || key;
    Object.entries(vars || {}).forEach(([name, value]) => {
        text = text.replaceAll('{' + name + '}', String(value));
    });
    return text;
}

function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([name, value]) => {
        if (value === undefined || value === null || value === false) return;
        if (name === 'class') node.className = value;
        else if (name === 'text') node.textContent = value;
        else if (name.startsWith('data-')) node.setAttribute(name, value);
        else if (name === 'value') node.value = value;
        else if (name === 'checked' || name === 'disabled' || name === 'selected') node[name] = !!value;
        else node.setAttribute(name, value);
    });
    (children || []).forEach((child) => {
        if (child === null || child === undefined) return;
        node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    });
    return node;
}

function actionHandlers() {
    return {
        'load-project': (node) => {
            state.project = node.value;
            state.editing = null;
            refresh();
        },
        'new-project': async () => {
            const name = window.prompt(t('board.projectPrompt'));
            if (!name || !name.trim()) return;
            try {
                const created = await client.post('/projects', { name: name.trim() });
                state.project = created.project.key;
                state.editing = null;
                await refresh();
            } catch (error) {
                state.error = t('board.error', { message: error.message });
                render();
            }
        },
        refresh: () => refresh(),
        'start-edit': (node) => {
            const entry = findEntry(node.dataset.ref);
            state.editing = { mode: 'edit', entry };
            render();
        },
        'start-create': (node) => {
            state.editing = { mode: 'create', status: node.dataset.status };
            render();
        },
        cancel: () => {
            state.editing = null;
            render();
        },
        save: (node) => {
            const form = node.closest('form');
            if (form) saveEntry(form.dataset.form);
        },
        remove: async (node) => {
            const ref = node.dataset.ref;
            if (!window.confirm(t('board.confirmDelete', { id: ref }))) return;
            try {
                await client.delete('/entries/' + encodeURIComponent(ref));
                await refresh();
            } catch (error) {
                state.error = t('board.error', { message: error.message });
                render();
            }
        },
        'move-status': async (node) => {
            try {
                await client.patch('/entries/' + encodeURIComponent(node.dataset.ref), {
                    status: node.value,
                });
                await refresh();
            } catch (error) {
                state.error = t('board.error', { message: error.message });
                render();
            }
        },
    };
}

function findEntry(ref) {
    for (const column of state.columns) {
        const match = column.entries.find((entry) => entry.id === ref);
        if (match) return match;
    }
    return null;
}

async function saveEntry(mode) {
    const form = root.querySelector('[data-form="' + mode + '"]');
    if (!form) return;
    const value = (name) => (form.querySelector('[name="' + name + '"]') || {}).value || '';
    const title = value('title').trim();
    if (!title) {
        state.error = t('board.titleRequired');
        render();
        return;
    }
    const payload = {
        title,
        content: value('content'),
        status: value('status'),
        priority: value('priority'),
        due: value('due'),
        labels: splitList(value('labels')),
        assignee: value('assignee').trim(),
        links: splitList(value('links')),
    };
    try {
        if (state.editing && state.editing.mode === 'edit') {
            await client.patch('/entries/' + encodeURIComponent(state.editing.entry.id), payload);
        } else {
            await client.post('/entries', { project: state.project, ...payload });
        }
        state.editing = null;
        state.error = '';
        await refresh();
    } catch (error) {
        state.error = t('board.error', { message: error.message });
        render();
    }
}

function splitList(text) {
    return String(text || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
}

// ---------------------------------------------------------------- loading

async function refresh() {
    await loadProjects();
    await loadBoard();
    render();
}

async function loadProjects() {
    try {
        const data = await client.get('/projects');
        state.projects = data.projects || [];
        if (!state.project && state.projects.length) {
            state.project = state.projects[0].key;
        }
        if (state.project && !state.projects.some((item) => item.key === state.project)) {
            state.project = state.projects.length ? state.projects[0].key : '';
        }
    } catch (error) {
        state.error = t('board.error', { message: error.message });
    }
}

async function loadBoard() {
    if (!state.project) {
        state.columns = [];
        return;
    }
    try {
        const data = await client.get('/board?project=' + encodeURIComponent(state.project));
        state.columns = data.columns || [];
        state.error = '';
    } catch (error) {
        state.error = t('board.error', { message: error.message });
        state.columns = [];
    }
}

// ---------------------------------------------------------------- render

function renderToolbar() {
    const options = state.projects.map((project) =>
        el('option', {
            value: project.key,
            text: project.key + ' — ' + project.name,
            selected: project.key === state.project,
        })
    );
    return el('div', { class: 'board-toolbar' }, [
        el('label', { class: 'board-field' }, [
            el('span', { text: t('board.projects') }),
            el('select', {
                'data-action': 'load-project',
                disabled: !state.projects.length,
            }, options),
        ]),
        el('button', { class: 'btn', 'data-action': 'new-project', text: t('board.newProject') }),
        el('button', { class: 'btn btn-secondary', 'data-action': 'refresh', text: t('board.refresh') }),
    ]);
}

function field(name, label, value, options) {
    const opts = options || {};
    const input = opts.multiline
        ? el('textarea', { name, rows: String(opts.rows || 3), value: value || '' })
        : el('input', { name, value: value || '', placeholder: opts.placeholder || '' });
    return el('label', { class: 'board-field' }, [
        el('span', { text: label }),
        input,
    ]);
}

function selectField(name, label, value, values) {
    return el('label', { class: 'board-field' }, [
        el('span', { text: label }),
        el('select', { name }, values.map((item) =>
            el('option', {
                value: item,
                text: COLUMN_LABELS[state.lang][item] || item.charAt(0).toUpperCase() + item.slice(1),
                selected: item === value,
            })
        )),
    ]);
}

function priorityField(value) {
    return el('label', { class: 'board-field' }, [
        el('span', { text: t('board.priority') }),
        el('select', { name: 'priority' }, PRIORITIES.map((item) =>
            el('option', {
                value: item,
                text: item.charAt(0).toUpperCase() + item.slice(1),
                selected: item === (value || 'medium'),
            })
        )),
    ]);
}

function entryForm(entry, status) {
    const isEdit = !!entry;
    return el('form', {
        class: 'board-form',
        'data-form': isEdit ? 'edit' : 'create',
    }, [
        field('title', t('board.title'), entry ? entry.title : ''),
        field('content', t('board.content'), entry ? entry.content : '', { multiline: true }),
        selectField('status', t('board.status'), entry ? entry.status : status, COLUMNS),
        priorityField(entry ? entry.priority : 'medium'),
        field('due', t('board.due'), entry ? entry.due || '' : '', { placeholder: 'YYYY-MM-DD' }),
        field('labels', t('board.labels'), entry ? (entry.labels || []).join(', ') : '', {
            placeholder: t('board.labelsHint'),
        }),
        field('assignee', t('board.assignee'), entry ? entry.assignee || '' : ''),
        field('links', t('board.links'), entry ? (entry.links || []).join(', ') : '', {
            placeholder: t('board.linksHint'),
        }),
        el('div', { class: 'board-form-actions' }, [
            el('button', { type: 'submit', class: 'btn', 'data-action': 'save', text: t('board.save') }),
            el('button', { type: 'button', class: 'btn btn-secondary', 'data-action': 'cancel', text: t('board.cancel') }),
        ]),
    ]);
}

function card(entry) {
    const editing = state.editing && state.editing.mode === 'edit'
        && state.editing.entry && state.editing.entry.id === entry.id;
    if (editing) {
        return el('article', { class: 'board-card board-card-editing' }, [entryForm(entry, entry.status)]);
    }
    const meta = [];
    if (entry.due) meta.push(el('span', { class: 'board-chip', text: entry.due }));
    meta.push(el('span', { class: 'board-chip board-priority-' + entry.priority, text: entry.priority }));
    if (entry.assignee) meta.push(el('span', { class: 'board-chip', text: '@' + entry.assignee }));
    (entry.labels || []).forEach((label) => meta.push(el('span', { class: 'board-chip board-label', text: label })));
    return el('article', { class: 'board-card', 'data-ref': entry.id }, [
        el('div', { class: 'board-card-head' }, [
            el('span', { class: 'board-ref', text: entry.id }),
            el('div', { class: 'board-card-actions' }, [
                el('button', { class: 'btn btn-link', 'data-action': 'start-edit', 'data-ref': entry.id, text: t('board.edit') }),
                el('button', { class: 'btn btn-link board-danger', 'data-action': 'remove', 'data-ref': entry.id, text: t('board.delete') }),
            ]),
        ]),
        el('h4', { class: 'board-card-title', text: entry.title }),
        entry.content ? el('p', { class: 'board-card-content', text: entry.content }) : null,
        el('div', { class: 'board-card-meta' }, meta),
        el('div', { class: 'board-card-links' }, (entry.links || []).map((link) =>
            el('a', { href: link, target: '_blank', rel: 'noopener noreferrer', text: link })
        )),
        el('label', { class: 'board-move' }, [
            el('span', { text: t('board.status') }),
            el('select', { 'data-action': 'move-status', 'data-ref': entry.id }, COLUMNS.map((status) =>
                el('option', {
                    value: status,
                    text: COLUMN_LABELS[state.lang][status],
                    selected: status === entry.status,
                })
            )),
        ]),
    ]);
}

function column(status) {
    const data = state.columns.find((item) => item.status === status) || { entries: [] };
    const entries = data.entries || [];
    const creating = state.editing && state.editing.mode === 'create'
        && state.editing.status === status;
    return el('section', { class: 'board-column board-column-' + status }, [
        el('header', { class: 'board-column-head' }, [
            el('h3', { text: COLUMN_LABELS[state.lang][status] }),
            el('span', { class: 'board-count', text: String(entries.length) }),
        ]),
        el('div', { class: 'board-column-body' },
            entries.length ? entries.map(card) : [el('p', { class: 'board-empty', text: t('board.empty') })]
        ),
        creating ? entryForm(null, status) : null,
        el('button', {
            class: 'btn btn-secondary board-add',
            'data-action': 'start-create',
            'data-status': status,
            text: t('board.add'),
        }),
    ]);
}

function render() {
    if (!root) return;
    root.replaceChildren();
    if (!state.projects.length) {
        root.appendChild(el('div', { class: 'board-empty-state' }, [
            el('p', { text: t('board.empty') }),
            el('button', { class: 'btn', 'data-action': 'new-project', text: t('board.newProject') }),
        ]));
        return;
    }
    root.appendChild(renderToolbar());
    if (state.error) {
        root.appendChild(el('p', { class: 'board-error', text: state.error }));
    }
    root.appendChild(el('div', { class: 'board-grid' }, COLUMNS.map(column)));
}

function onClick(event) {
    const target = event.target.closest('[data-action]');
    if (!target || !root.contains(target)) return;
    // A <select> reports through its change event; handling the click too
    // would run the action twice, once with the previous value.
    if (target.tagName === 'SELECT') return;
    const handlers = actionHandlers();
    const handler = handlers[target.dataset.action];
    if (!handler) return;
    if (target.dataset.action === 'save') {
        event.preventDefault();
    }
    handler(target, event);
}

function onChange(event) {
    const target = event.target.closest('[data-action]');
    if (!target || !root.contains(target)) return;
    const handler = actionHandlers()[target.dataset.action];
    if (!handler) return;
    handler(target, event);
}

function onSubmit(event) {
    const form = event.target.closest('form[data-form]');
    if (!form || !root.contains(form)) return;
    event.preventDefault();
    saveEntry(form.dataset.form);
}

// ---------------------------------------------------------------- contract

export async function register({ container, api, i18n }) {
    root = container;
    client = api;
    state.lang = (i18n && i18n.lang) === 'zh' ? 'zh' : 'en';
    root.addEventListener('click', onClick);
    root.addEventListener('change', onChange);
    root.addEventListener('submit', onSubmit);
    render();
    await refresh();

    const switcher = document.getElementById('langSwitcher');
    if (switcher) {
        onLanguageChange = () => {
            state.lang = switcher.value === 'zh' ? 'zh' : 'en';
            render();
        };
        switcher.addEventListener('change', onLanguageChange);
    }
}

export function unmount() {
    if (root) {
        root.removeEventListener('click', onClick);
        root.removeEventListener('change', onChange);
        root.removeEventListener('submit', onSubmit);
    }
    const switcher = document.getElementById('langSwitcher');
    if (switcher && onLanguageChange) {
        switcher.removeEventListener('change', onLanguageChange);
    }
    onLanguageChange = null;
    root = null;
    client = null;
}
