const fs = require('fs').promises;
const path = require('path');

// Helper function to resolve path based on file_type
function getResolvedPath(basePath, fileType, relativePath) {
    let targetDir = '';
    // Corrected directory names to match project structure
    if (fileType === 'diary') {
        targetDir = 'dailynote';
    } else if (fileType === 'agent') {
        targetDir = 'Agent';
    }

    // If a fileType is specified, treat relativePath as relative to that directory.
    // Otherwise, treat it as relative to the project base path.
    const fullPath = path.resolve(basePath, targetDir, relativePath);
    const safeBasePath = path.resolve(basePath);

    // Security check to prevent path traversal attacks
    if (!fullPath.startsWith(safeBasePath)) {
        throw new Error("Access denied. Path is outside the project directory.");
    }
    return fullPath;
}

async function main() {
    try {
        const projectBasePath = process.env.PROJECT_BASE_PATH || process.cwd();
        const input = await readStdin();
        const args = JSON.parse(input);

        const { command, file_type, file_path, dir_path, content, character_name } = args;

        let result;
        switch (command) {
            case 'ReadFile':
                result = await readFile(projectBasePath, file_type, file_path);
                break;
            case 'WriteFile':
                result = await writeFile(projectBasePath, fileBasePath, file_type, file_path, content);
                break;
            case 'DeleteFile':
                result = await deleteFile(projectBasePath, file_type, file_path, character_name);
                break;
            case 'ListDirectory':
                result = await listDirectory(projectBasePath, file_type, dir_path);
                break;
            default:
                throw new Error(`Unknown command: ${command}`);
        }

        await writeStdout({ status: 'success', result });

    } catch (error) {
        await writeStdout({ status: 'error', error: error.message });
        process.exit(1);
    }
}

function readStdin() {
    return new Promise((resolve) => {
        let data = '';
        process.stdin.on('data', chunk => data += chunk);
        process.stdin.on('end', () => resolve(data));
    });
}

function writeStdout(data) {
    return new Promise((resolve) => {
        process.stdout.write(JSON.stringify(data), () => resolve());
    });
}

async function readFile(basePath, fileType, filePath) {
    if (!filePath) {
        throw new Error("Missing required parameter 'file_path'.");
    }
    const resolvedPath = getResolvedPath(basePath, fileType, filePath);
    const content = await fs.readFile(resolvedPath, 'utf-8');
    return `Content of ${filePath}:
${content}`;
}

async function writeFile(basePath, fileType, filePath, content) {
    if (!filePath || content === undefined) {
        throw new Error("Missing required parameters 'file_path' or 'content'.");
    }
    const resolvedPath = getResolvedPath(basePath, fileType, filePath);
    await fs.writeFile(resolvedPath, content, 'utf-8');
    return `Successfully wrote to ${filePath}.`;
}

async function deleteFile(basePath, fileType, filePath, characterName) {
    // Enhanced logic: If no specific file path is given, but we have a character and a type, list possible files.
    if (!filePath && characterName && (fileType === 'diary' || fileType === 'agent')) {
        let dirToList;
        let files;
        let promptMessage;

        if (fileType === 'diary') {
            dirToList = path.join('dailynote', characterName);
            promptMessage = `Which diary of '${characterName}' would you like to delete? Please choose one and use its full path in the next command.`;
        } else { // fileType === 'agent'
            dirToList = 'Agent';
            promptMessage = `Which agent file would you like to delete? The agent file for '${characterName}' is likely '${characterName}.txt'. Please choose one and use its full path in the next command.`;
        }

        try {
            // Re-use the ListDirectory logic to get the file list string
            files = await listDirectory(basePath, null, dirToList); // fileType is null because dirToList is already a full relative path
            return `${promptMessage}\n\n${files}`;
        } catch (e) {
             if (e.code === 'ENOENT') {
                throw new Error(`Directory not found: '${dirToList}'. Cannot list files for character '${characterName}'.`);
            }
            throw e;
        }
    }

    if (!filePath) {
        throw new Error("Missing required parameter 'file_path'. Provide 'file_path' or 'character_name' with 'file_type'.");
    }
    const resolvedPath = getResolvedPath(basePath, fileType, filePath);
    await fs.unlink(resolvedPath);
    return `Successfully deleted ${filePath}.`;
}

async function listDirectory(basePath, fileType, dirPath) {
    if (!dirPath) {
        throw new Error("Missing required parameter 'dir_path'.");
    }
    // In the context of deleteFile, fileType is null and dirPath is already constructed.
    // In the context of a direct ListDirectory call, fileType might be used.
    const resolvedPath = getResolvedPath(basePath, fileType, dirPath);
    const files = await fs.readdir(resolvedPath);
    return `Files in '${dirPath}':\n${files.join('\n')}`;
}

main();