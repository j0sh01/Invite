import { ref } from 'vue'
import { frappeRequest } from '@/utils/api'

let _roleInfoCache = null
let _fetching = null

export function useRoleInfo() {
  async function getRoleInfo() {
    if (_roleInfoCache) return _roleInfoCache
    if (_fetching) return _fetching

    _fetching = frappeRequest({ url: 'invite.api.session.get_user_role_info' })
      .then((info) => {
        _roleInfoCache = info
        _fetching = null
        return _roleInfoCache
      })
      .catch(() => {
        _roleInfoCache = { is_frontdesk_only: false, frontdesk_role: '', user_roles: [] }
        _fetching = null
        return _roleInfoCache
      })

    return _fetching
  }

  return { getRoleInfo }
}
