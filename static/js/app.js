const { createApp, ref, computed, onMounted } = Vue;

createApp({
    setup() {
        const presetSizes = ref([]);
        const selectedSizes = ref([]);
        const customSizes = ref([]);
        const customWidth = ref(null);
        const customHeight = ref(null);
        const cropDirection = ref('auto');
        const outputFormat = ref('jpeg');  // 输出格式
        const uploadedFiles = ref([]);
        const isDragging = ref(false);
        const isProcessing = ref(false);
        const downloadUrl = ref('');
        const error = ref('');

        const allSizes = computed(() => {
            return [...selectedSizes.value, ...customSizes.value];
        });

        const canExport = computed(() => {
            return uploadedFiles.value.length > 0 && allSizes.value.length > 0;
        });

        onMounted(async () => {
            try {
                const res = await fetch('/api/sizes');
                const data = await res.json();
                presetSizes.value = data.sizes;
            } catch (e) {
                error.value = '获取预设尺寸失败';
            }
        });

        async function handleFileSelect(e) {
            const files = Array.from(e.target.files);
            await uploadFiles(files);
        }

        async function handleDrop(e) {
            isDragging.value = false;
            const files = Array.from(e.dataTransfer.files);
            await uploadFiles(files);
        }

        async function uploadFiles(files) {
            const formData = new FormData();
            files.forEach(file => {
                if (file.type.startsWith('image/')) {
                    formData.append('files', file);
                }
            });

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                uploadedFiles.value.push(...data.files);
            } catch (e) {
                error.value = '上传失败';
            }
        }

        function removeFile(id) {
            uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id);
            fetch('/api/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileIds: [id] })
            });
        }

        function addCustomSize() {
            if (customWidth.value && customHeight.value) {
                customSizes.value.push({
                    width: customWidth.value,
                    height: customHeight.value
                });
                customWidth.value = null;
                customHeight.value = null;
            }
        }

        function removeCustomSize(index) {
            customSizes.value.splice(index, 1);
        }

        async function processImages() {
            if (!canExport.value) return;

            isProcessing.value = true;
            error.value = '';
            downloadUrl.value = '';

            try {
                const res = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fileIds: uploadedFiles.value.map(f => f.id),
                        sizes: allSizes.value,
                        cropDirection: cropDirection.value,
                        outputFormat: outputFormat.value
                    })
                });
                const data = await res.json();
                if (data.downloadUrl) {
                    downloadUrl.value = data.downloadUrl;
                } else {
                    error.value = data.error || '处理失败';
                }
            } catch (e) {
                error.value = '处理失败';
            } finally {
                isProcessing.value = false;
            }
        }

        return {
            presetSizes,
            selectedSizes,
            customSizes,
            customWidth,
            customHeight,
            cropDirection,
            outputFormat,
            uploadedFiles,
            isDragging,
            isProcessing,
            downloadUrl,
            error,
            allSizes,
            canExport,
            handleFileSelect,
            handleDrop,
            removeFile,
            addCustomSize,
            removeCustomSize,
            processImages
        };
    }
}).mount('#app');
