# Computer Systems Knowledge Pack

## Virtual Memory

Virtual memory is an abstraction that gives each process the illusion of a large, private, contiguous address space. The operating system and hardware memory management unit translate virtual addresses to physical addresses through page tables. Virtual memory supports protection between processes, controlled sharing, demand paging, and efficient use of physical memory. When a referenced page is not resident in physical memory, a page fault transfers control to the operating system so the page can be loaded or the access can be rejected.

## Processes and Context Switching

A process is an instance of a running program together with its private virtual address space, open files, register state, and other operating-system resources. The operating system schedules processes on CPUs and switches between them by saving the current context and restoring another context. Context switching lets multiple programs share processors, but it has overhead because registers, page-table state, and cache locality may change.

## Cache Memory

Cache memory is a small and fast storage layer placed close to the processor. It exploits temporal locality, where recently used data is likely to be used again, and spatial locality, where nearby data is likely to be used soon. Caches are usually organized into sets and lines; a miss occurs when requested data is not present and must be fetched from a lower level of the memory hierarchy.

## Exceptional Control Flow

Exceptional control flow is any abrupt change in the normal sequence of instruction execution. Hardware exceptions, interrupts, traps, faults, process context switches, and Unix signals are examples. Exceptional control flow allows operating systems to respond to I/O events, system calls, arithmetic errors, page faults, and interprocess communication while preserving a controlled execution model.

## Amdahl's Law

Amdahl's Law estimates the maximum speedup from optimizing part of a system. If fraction p of execution time can be improved by a factor s, total speedup is 1 / ((1 - p) + p / s). The law shows that the non-optimized portion eventually dominates performance, so optimization effort should focus on the common case and on bottlenecks with large execution share.

## Retrieval-Augmented Generation

Retrieval-augmented generation, or RAG, answers a question by retrieving relevant evidence from an external knowledge base and then conditioning generation on that evidence. In a grounded educational agent, RAG reduces hallucination by requiring answers to cite retrieved passages. The main retrieval quality metric used in this project is Hit@5, which is true when at least one of the top five retrieved chunks matches the annotated evidence.
