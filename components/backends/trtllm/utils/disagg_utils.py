# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import logging

from tensorrt_llm.llmapi import DisaggregatedParams

# Configure logging for disaggregated params operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DisaggregatedParamsCodec:
    """
    Codec for encoding and decoding disaggregated params for network transfer.
    """

    @staticmethod
    def decode(
        disaggregated_params: DisaggregatedParams,
    ) -> DisaggregatedParams:
        if disaggregated_params is None:
            logger.debug("🔄 DisaggregatedParamsCodec.decode: Input is None")
            return None

        logger.info("=" * 50)
        logger.info("🔓 DECODING DISAGGREGATED PARAMETERS")
        logger.info("=" * 50)
        logger.info("📥 Input parameters:")
        logger.info(f"   ➜ Request type: {disaggregated_params.request_type}")
        logger.info(f"   ➜ Context request ID: {disaggregated_params.ctx_request_id}")
        logger.info(f"   ➜ First gen tokens: {disaggregated_params.first_gen_tokens}")
        logger.info(f"   ➜ Draft tokens: {disaggregated_params.draft_tokens}")

        opaque_state_size = (
            len(disaggregated_params.opaque_state)
            if disaggregated_params.opaque_state
            else 0
        )
        logger.info(f"   ➜ Encoded opaque state size: {opaque_state_size} characters")

        opaque_state = (
            base64.b64decode(disaggregated_params.opaque_state)
            if disaggregated_params.opaque_state is not None
            else None
        )

        decoded_state_size = len(opaque_state) if opaque_state else 0
        logger.info(f"🔄 Decoded opaque state size: {decoded_state_size} bytes")
        logger.info("✅ Disaggregated parameters successfully decoded")

        return DisaggregatedParams(
            request_type=disaggregated_params.request_type,
            first_gen_tokens=disaggregated_params.first_gen_tokens,
            ctx_request_id=disaggregated_params.ctx_request_id,
            opaque_state=opaque_state,
            draft_tokens=disaggregated_params.draft_tokens,
        )

    @staticmethod
    def encode(
        disaggregated_params: DisaggregatedParams,
    ) -> DisaggregatedParams:
        if disaggregated_params is None:
            logger.debug("🔄 DisaggregatedParamsCodec.encode: Input is None")
            return None

        logger.info("=" * 50)
        logger.info("🔒 ENCODING DISAGGREGATED PARAMETERS")
        logger.info("=" * 50)
        logger.info("📤 Input parameters:")
        logger.info(f"   ➜ Request type: {disaggregated_params.request_type}")
        logger.info(f"   ➜ Context request ID: {disaggregated_params.ctx_request_id}")
        logger.info(f"   ➜ First gen tokens: {disaggregated_params.first_gen_tokens}")
        logger.info(f"   ➜ Draft tokens: {disaggregated_params.draft_tokens}")

        raw_state_size = (
            len(disaggregated_params.opaque_state)
            if disaggregated_params.opaque_state
            else 0
        )
        logger.info(f"   ➜ Raw opaque state size: {raw_state_size} bytes")

        encoded_opaque_state = (
            base64.b64encode(disaggregated_params.opaque_state).decode("utf-8")
            if disaggregated_params.opaque_state is not None
            else None
        )

        encoded_state_size = len(encoded_opaque_state) if encoded_opaque_state else 0
        logger.info(f"🔄 Encoded opaque state size: {encoded_state_size} characters")
        logger.info(
            "✅ Disaggregated parameters successfully encoded for network transfer"
        )

        return DisaggregatedParams(
            request_type=disaggregated_params.request_type,
            first_gen_tokens=disaggregated_params.first_gen_tokens,
            ctx_request_id=disaggregated_params.ctx_request_id,
            opaque_state=encoded_opaque_state,
            draft_tokens=disaggregated_params.draft_tokens,
        )
