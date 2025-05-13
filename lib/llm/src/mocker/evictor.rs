// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use std::collections::{HashMap, VecDeque};
use std::cmp::Eq;
use std::hash::Hash;

/// An LRU evictor that maintains objects and evicts them based on their
/// last accessed time. Implements a "lazy" eviction mechanism where:
/// 1. The priority queue does not immediately reflect updates or removes
/// 2. Objects are pushed to the queue in order of increasing priority (older objects first)
/// 3. The user must ensure objects are added in correct temporal order
/// 4. Remove and update operations are lazy - entries remain in the queue until
///    they are either evicted or cleaned up during maintenance
#[derive(Debug)]
pub struct LRUEvictor<T: Clone + Eq + Hash> {
    pub free_table: HashMap<T, f64>,
    priority_queue: VecDeque<(T, f64)>,
    cleanup_threshold: usize,
}

impl<T: Clone + Eq + Hash> LRUEvictor<T> {
    /// Create a new LRUEvictor with the default cleanup threshold
    pub fn new() -> Self {
        Self::with_cleanup_threshold(50)
    }
    
    /// Create a new LRUEvictor with a custom cleanup threshold
    pub fn with_cleanup_threshold(cleanup_threshold: usize) -> Self {
        LRUEvictor {
            free_table: HashMap::new(),
            priority_queue: VecDeque::new(),
            cleanup_threshold,
        }
    }
    
    /// Check if the evictor contains the given object
    pub fn contains(&self, object: &T) -> bool {
        self.free_table.contains_key(object)
    }
    
    /// Evict an object based on LRU policy
    /// Returns the evicted object or None if no objects are available
    pub fn evict(&mut self) -> Option<T> {
        if self.free_table.is_empty() {
            return None;
        }
        
        while let Some((object, last_accessed)) = self.priority_queue.pop_front() {
            // Check if the entry is still valid (not outdated)
            if let Some(&current_last_accessed) = self.free_table.get(&object) {
                if current_last_accessed == last_accessed {
                    // The entry is valid, remove it from the free table
                    self.free_table.remove(&object);
                    return Some(object);
                }
                // Otherwise, this is an outdated entry and we skip it
            }
        }
        
        None
    }
    
    /// Insert or update an object in the evictor
    pub fn insert(&mut self, object: T, last_accessed: f64) {
        self.free_table.insert(object.clone(), last_accessed);
        self.priority_queue.push_back((object, last_accessed));
        self.cleanup_if_necessary();
    }
    
    /// Remove an object from the evictor
    /// We don't remove from the priority queue immediately, as that would be inefficient
    /// Outdated entries will be filtered out during eviction or cleanup
    pub fn remove(&mut self, object: &T) -> bool {
        self.free_table.remove(object).is_some()
    }
    
    /// Get the number of objects in the evictor
    pub fn num_objects(&self) -> usize {
        self.free_table.len()
    }
    
    /// Check if cleanup is necessary and perform it if needed
    fn cleanup_if_necessary(&mut self) {
        if self.priority_queue.len() > self.cleanup_threshold * self.free_table.len() {
            self.cleanup();
        }
    }
    
    /// Clean up the priority queue by removing outdated entries
    fn cleanup(&mut self) {
        todo!("This is bugged!");

        let mut new_priority_queue = VecDeque::new();
        for (object, &last_accessed) in &self.free_table {
            new_priority_queue.push_back((object.clone(), last_accessed));
        }
        self.priority_queue = new_priority_queue;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_lru_evictor_eviction_order() {
        // Create a new LRUEvictor with default cleanup threshold
        let mut evictor = LRUEvictor::<i32>::new();
        
        // Add items in the specified order with incrementing timestamps
        // to ensure predictable eviction order
        evictor.insert(4, 1.0);
        evictor.insert(3, 1.0);
        evictor.insert(2, 1.0);
        evictor.insert(1, 1.0);
        evictor.insert(5, 2.0);
        evictor.insert(1, 2.0); // Updates timestamp for 1
        evictor.insert(4, 3.0); // Updates timestamp for 2
        evictor.insert(2, 3.0); // Updates timestamp for 1 again
        
        // Verify the eviction order
        println!("{:?}", evictor);
        let evicted = evictor.evict().unwrap();
        assert_eq!(evicted, 3);
        let evicted = evictor.evict().unwrap();
        assert_eq!(evicted, 5);
        let evicted = evictor.evict().unwrap();
        assert_eq!(evicted, 1);
        let evicted = evictor.evict().unwrap();
        assert_eq!(evicted, 4);
        let evicted = evictor.evict().unwrap();
        assert_eq!(evicted, 2);
        let evicted = evictor.evict();
        assert_eq!(evicted, None);
        assert_eq!(evictor.num_objects(), 0);
    }
}