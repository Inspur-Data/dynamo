use super::*;
use crate::block_manager::pool::{AsyncPoolController, PoolStatus};
use futures::stream;
use serde_json::Value;

impl<Locality: LocalityProvider, Metadata: BlockMetadata> ControllerHandler<Locality, Metadata> {
    pub fn new(block_manager: KvBlockManager<Locality, Metadata>) -> Arc<Self> {
        Arc::new(Self { block_manager })
    }

    fn get_pool_controller(&self, cache_level: &CacheLevel) -> Result<&dyn AsyncPoolController> {
        match cache_level {
            CacheLevel::G1 => Ok(self
                .block_manager
                .device()
                .ok_or_else(|| anyhow::anyhow!("Device pool not found"))?),
            CacheLevel::G2 => Ok(self
                .block_manager
                .host()
                .ok_or_else(|| anyhow::anyhow!("Host pool not found"))?),
            CacheLevel::G3 => Ok(self
                .block_manager
                .disk()
                .ok_or_else(|| anyhow::anyhow!("Disk pool not found"))?),
        }
    }

    async fn reset_pool(&self, cache_level: &CacheLevel) -> Result<()> {
        Ok(self.get_pool_controller(cache_level)?.reset().await?)
    }

    async fn handle_status(&self, cache_level: &CacheLevel) -> Result<PoolStatus> {
        let pool_controller = self.get_pool_controller(cache_level)?;
        Ok(pool_controller.status().await?)
    }

    async fn handle_reset(&self, request: ResetRequest) -> Result<()> {
        let (cache_level, sequence_hashes) = request.dissolve();
        match sequence_hashes {
            Some(sequence_hashes) => {
                self.reset_blocks(cache_level, sequence_hashes).await?;
                Ok(())
            }
            None => self.reset_pool(&cache_level).await,
        }
    }

    async fn handle_reset_all(&self) -> Result<()> {
        for cache_level in &[CacheLevel::G1, CacheLevel::G2, CacheLevel::G3] {
            if let Some(pool_controller) = self.get_pool_controller(cache_level).ok() {
                pool_controller.reset().await?;
            }
        }
        Ok(())
    }

    async fn reset_blocks(
        &self,
        cache_level: CacheLevel,
        sequence_hashes: Vec<SequenceHash>,
    ) -> Result<()> {
        let pool_controller = self.get_pool_controller(&cache_level)?;
        unimplemented!("reset blocks")
    }
}

#[async_trait]
impl<Locality: LocalityProvider, Metadata: BlockMetadata>
    AsyncEngine<HandlerInput, HandlerOutput, Error> for ControllerHandler<Locality, Metadata>
{
    async fn generate(&self, input: HandlerInput) -> Result<HandlerOutput> {
        let (data, ctx) = input.into_parts();

        let annotated = match data {
            ControlMessage::Status(cache_level) => {
                // handle status
                make_response(self.handle_status(&cache_level).await)
            }

            ControlMessage::Reset(request) => {
                // handle reset
                make_unit_response(self.handle_reset(request).await)
            }

            ControlMessage::ResetAll => make_unit_response(self.handle_reset_all().await),
        };

        let stream = stream::once(async move { annotated });
        Ok(ResponseStream::new(Box::pin(stream), ctx.context()))
    }
}

fn make_unit_response(response: Result<()>) -> Annotated<Value> {
    match response {
        Ok(()) => Annotated::from_data(serde_json::Value::Null),
        Err(e) => Annotated::from_error(e.to_string()),
    }
}

fn make_response<T: Serialize>(response: Result<T>) -> Annotated<Value> {
    match response {
        Ok(response) => match serde_json::to_value(response) {
            Ok(values) => Annotated::from_data(values),
            Err(e) => Annotated::from_error(e.to_string()),
        },
        Err(e) => Annotated::from_error(e.to_string()),
    }
}
