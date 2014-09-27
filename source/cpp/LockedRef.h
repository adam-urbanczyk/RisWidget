// The MIT License (MIT)
//
// Copyright (c) 2014 Erik Hvatum
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#pragma once

#include "Common.h"

template<typename RefT, typename MutexT = QMutex>
class LockedRef
{
public:
    enum LockDispositionAtConstruction
    {
        PreLocked,
        GetLock
    };

    LockedRef(RefT& ref, MutexT& lock,
              const LockDispositionAtConstruction& lockDispositionAtConstruction = GetLock);
    ~LockedRef();
    LockedRef(const LockedRef&) = delete;
    LockedRef& operator = (const LockedRef&) = delete;

    bool operator == (const LockedRef& rhs) const;
    bool operator != (const LockedRef& rhs) const;
    RefT& ref() const;

protected:
    RefT& m_ref;
    MutexT& m_lock;
};

template<typename RefT, typename MutexT>
LockedRef<RefT, MutexT>::LockedRef(RefT& ref, MutexT& lock,
                                   const LockDispositionAtConstruction& lockDispositionAtConstruction)
  : m_ref(ref),
    m_lock(lock)
{
    if(lockDispositionAtConstruction == GetLock)
    {
        m_lock.lock();
    }
}

template<typename RefT, typename MutexT>
LockedRef<RefT, MutexT>::~LockedRef()
{
    m_lock.unlock();
}

template<typename RefT, typename MutexT>
bool LockedRef<RefT, MutexT>::operator == (const LockedRef<RefT, MutexT>& rhs) const
{
    return m_ref == rhs.m_ref;
}

template<typename RefT, typename MutexT>
bool LockedRef<RefT, MutexT>::operator != (const LockedRef<RefT, MutexT>& rhs) const
{
    return m_ref != rhs.m_ref;
}

template<typename RefT, typename MutexT>
RefT& LockedRef<RefT, MutexT>::ref() const
{
    return m_ref;
}
