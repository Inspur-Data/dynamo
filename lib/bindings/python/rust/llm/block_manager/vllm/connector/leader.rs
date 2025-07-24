use super::*;

pub struct KvConnectorLeader {}

impl KvConnectorLeader {
    // Connector API

    pub fn get_num_new_matched_tokens(
        &self,
        request_id: String,
        num_computed_tokens: u64,
    ) -> (u64, bool) {
        unimplemented!()
    }

    /// We drop the need to pass in the KvCacheBlocks and the num_external_tokens as they are captured
    /// statefully in the [`VllmLeaderKvCacheManagerAndConnector::get_num_new_matched_tokens`] function.
    pub fn update_state_after_alloc(
        &mut self,
        request_id: String,
        block_ids: Vec<BlockId>,
        num_external_tokens: u64,
    ) {
        unimplemented!()
    }

    pub fn build_connector_metadata(
        &self,
        scheduler_output: SchedulerOutput,
    ) -> KvConnectorMetadata {
        unimplemented!()
    }

    pub fn request_finished(&mut self, request_id: String, block_ids: Vec<BlockId>) -> bool {
        unimplemented!()
    }

    // Helper functions

    pub fn create_slot(&self, request: KvbmRequest, tokens: Vec<u32>) -> PyResult<()> {
        let mut slot_manager = self.slot_manager.lock().map_err(to_pyerr)?;

        slot_manager
            .create_slot(&request.request_id, request.salt_hash, tokens)
            .map_err(to_pyerr)
    }
}
